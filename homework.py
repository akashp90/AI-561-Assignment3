import re
from collections.abc import Iterable
import copy


def flatten(xs):
    for x in xs:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x


class Predicate:
    def __init__(self, term_string, ground_truth=False):
        if term_string[0] == "~":
            self.sign = "N"
        else:
            self.sign = "P"
        self.name = term_string.split("(")[0]
        self.name.replace("~", "")
        # This returns '(x, y, z)'; So remove the bracks and get args seperately
        self.arguments = (
            re.findall(r"\(.*?\)", term_string)[0]
            .replace("(", "")
            .replace(")", "")
            .split(",")
        )
        self.term_string = term_string.strip()

        self.ground_truth = ground_truth

    def negate(self):
        self.sign = reverse_sign(self.sign)

    def __str__(self):
        # desc_string = "Name: " + str(self.name) + "; Arguments: " + str(self.arguments) + "; Sign: " + str(self.sign)
        if self.sign == "N":
            sign_string = "~"
        elif self.sign == "P":
            sign_string = ""
        return sign_string + self.term_string
        # return desc_string

    def get_predicate_name(self):
        return self.name.strip()


class PredicateListIterator:
    """Iterator class"""

    def __init__(self, predicate_list):
        # Team object reference
        self._predicate_list = predicate_list
        # member variable to keep track of current index
        self._index = 0

    def __next__(self):
        """'Returns the next value from predicate_list object's lists"""
        if self._index < (len(self._predicate_list.predicates)):
            result = self._predicate_list.predicates[self._index]
            self._index += 1
            return result
        # End of Iteration
        raise StopIteration


class PredicateList:
    def __init__(self, predicates, operator=None, sign="P"):
        self.predicates = predicates
        self.operator = operator
        self.sign = sign

    def get_predicate_name(self):
        predicate_names = []
        for p in self.predicates:
            predicate_names.append(p.get_predicate_name())

        return predicate_names

    def get_matching_predicate_by_name(self, predicate_name):
        # print("Self")
        # print(self)
        # print("Self predicates")
        # print(str(self.predicates))
        for predicate in self.predicates:
            # print("Checking for: " + str(predicate.get_predicate_name()))
            if isinstance(predicate, Predicate):
                # print("Checking for one:" + str(predicate.get_predicate_name()))
                if predicate.get_predicate_name() == predicate_name:
                    return predicate
            else:
                # print("Checking for list: " + str(predicate.get_predicate_name()))
                predicate.get_matching_predicate_by_name(predicate_name)

        return None

    def negate(self):
        for p in self.predicates:
            p.negate()

        # self.sign = reverse_sign(self.sign)
        if self.operator == "&":
            self.operator = "|"
        elif self.operator == "|":
            self.operator = "&"

    def __str__(self):
        s = ""
        if self.sign == "N":
            s = "~"

        s = s + "{"
        for p in self.predicates:
            s = s + str(p) + " " + str(self.operator) + " "

        if self.operator:
            rev = s[::-1]
            rev_op = self.operator[::-1]
            rev = rev.replace(rev_op, "", 1)
            s = rev[::-1]
        s = s + "}"
        return s

    def __add__(self, other):
        return self.predicates + other.predicates

    def __iter__(self):
        """Returns the Iterator object"""
        return PredicateListIterator(self)

    def __len__(self):
        return len(self.predicates)


def reverse_sign(sign):
    if sign == "P":
        return "N"
    else:
        return "P"


class Sentence:
    premise = None
    implication = None
    predicate_names = []

    def __init__(self, sentence_string):
        self.predicate_list = self.get_predicate_list(sentence_string)
        self.sentence_string = sentence_string

    def convert_to_cnf(self, suggestions=None):
        if suggestions is not None and suggestions[0] == "TAKE_NEGATION_INWARD":
            self.negate()

        cnf_check, suggestion = self.is_in_cnf()
        
        if not cnf_check and suggestion == "DISTRIBUTE" and self.predicate_list.operator == '|':
            new_pl_lists = []
            for i in range(0, len(self.predicate_list) - 1):
                p1 = self.predicate_list.predicates[0]
                p2 = self.predicate_list.predicates[i+1]
                if isinstance(p1, PredicateList) and isinstance(p2, Predicate):
                    for ip in p1.predicates:
                        new_predicate_list = PredicateList([ip, p2], '|')
                        new_pl_lists.append(new_predicate_list)

            new_pl = PredicateList(new_pl_lists, '&')
            self.predicate_list = new_pl


    def is_in_cnf(self):
        p_names = list(flatten(self.predicate_list.get_predicate_name()))
        print("Checking for")
        print(self.predicate_list.get_predicate_name())
        
        suggestions = []
        if len(p_names) == 1:
            return True, []

        if (
            len(p_names) == 2
            and self.predicate_list.operator == "|"
            and self.predicate_list.sign == "P"
        ):
            return True, []

        if self.predicate_list.sign == 'N':
            return (False, "TAKE_NEGATION_INWARD")

        sentence_string = str(self)
        if (len(p_names) > 2
            and '&' not in sentence_string):
            return True, []

        for p in self.predicate_list.predicates:
            if isinstance(p, Predicate) and self.predicate_list.operator == '&':
                return True, []
            if isinstance(p, PredicateList):
                if p.operator == '|':
                    return True, []
                else:
                    return (False, "DISTRIBUTE")

        return False, []


    def negate(self):
        self.predicate_list.negate()

    def remove_implication_sign(self):
        # Remove implication sign
        if self.predicate_list.operator == "=>":
            # a => b == ~a | b
            self.predicate_list.predicates[0].negate()
            self.predicate_list.operator = "|"

    def get_predicate_names(self):
        predicate_names = []
        for predicate in self.predicate_list:
            predicate_names.append(predicate.get_predicate_name())

        self.predicate_names = list(flatten(predicate_names))
        return self.predicate_names

    def get_predicate_list(self, sentence_string):
        predicate_terms = []
        predicates = []

        if "=>" in sentence_string:
            premise, conclusion = sentence_string.split("=>")
            if self.is_predicate(premise):
                predicate_terms.append(Predicate(premise))
            else:
                predicate_terms.append(self.get_predicate_list(premise))

            if self.is_predicate(conclusion):
                predicate_terms.append(Predicate(conclusion))
            else:
                x = self.get_predicate_list(conclusion)
                predicate_terms.append(x)

            predicate_list = PredicateList(predicate_terms, "=>")
            return predicate_list

        if "&" in sentence_string:
            anded_terms = sentence_string.split("&")
            for term in anded_terms:
                if self.is_predicate(term):
                    predicate_terms.append(Predicate(term))
                else:
                    predicate_terms.append(self.get_predicate_list(term))

            predicate_list = PredicateList(predicate_terms, "&")
            return predicate_list

        if "|" in sentence_string:
            ored_terms = sentence_string.split("|")
            for term in ored_terms:
                if self.is_predicate(term):
                    predicate_terms.append(Predicate(term))
                else:
                    predicate_terms.append(self.get_predicate_list(term))

            predicate_list = PredicateList(predicate_terms, "|")
            return predicate_list

        # No operatos present, atomic sentence
        return PredicateList([Predicate(sentence_string, ground_truth=True)])

    def is_predicate(self, term):
        if not any([x in term for x in ["&", "|", "=>"]]):
            return True
        else:
            return False

    def __str__(self):
        # print("Predicates" + str(type(self.predicates)))
        return str(self.predicate_list)


def apply_resolution(kb, query):
    query_predicate_name = query.predicate_list.predicates[0].name
    # print("query: " + str(query_predicate_name))

    for sentence in kb:
        # print("Searching in " + str(sentence))
        matched_predicate = sentence.predicate_list.get_matching_predicate_by_name(
            query_predicate_name
        )
        if matched_predicate is not None:
            print("Found a match")
            print(matched_predicate)
            return


file = open("some_input.txt", "r")
file_lines = file.readlines()
query_string = file_lines[0].strip()
number_of_sentences = int(file_lines[1].strip())

sentences = []

for i in range(2, 2 + number_of_sentences):
    sentences.append(file_lines[i].strip())


knowledge_base = []
for sentence in sentences:
    s = Sentence(sentence)
    print("For sentence: " + sentence)
    print(s)
    if "=>" in sentence:
        print("Removing implication")
        s.remove_implication_sign()
        print("After removing:")
        print(s)
    cnf, suggestions = s.is_in_cnf()
    if not cnf:
        print("Sentence is not in CNF")
        s.convert_to_cnf(suggestions)
    else:
        print("Sentence is in CNF")

    knowledge_base.append(s)


# main_knowledge_base = copy.deepcopy(knowledge_base)
# query_sentence = Sentence(query_string)

# query_sentence.negate()
# knowledge_base.append(query_sentence)

# apply_resolution(main_knowledge_base, query_sentence)
