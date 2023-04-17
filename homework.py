import re
from collections.abc import Iterable
import copy

# TODO: Handle whitespaces??

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
        self.name = self.name.replace("~", "")
        # This returns '(x, y, z)'; So remove the bracks and get args seperately
        self.arguments = (
            re.findall(r"\(.*?\)", term_string)[0]
            .replace("(", "")
            .replace(")", "")
            .split(",")
        )
        self.term_string = term_string.strip()
        self.ground_truth = ground_truth

    def is_variable():
        pass

    def negate(self):
        self.sign = reverse_sign(self.sign)

    def __str__(self):
        if self.sign == "N":
            sign_string = "~"
        elif self.sign == "P":
            sign_string = ""

        s = sign_string + self.name + "("

        for arg in self.arguments:
            s = s + arg + ", "

        s = s.rstrip(", ")
        s = s + ")"

        return s
        # return desc_string

    def get_predicate_name(self):
        return self.name.strip()

    def apply_substitutions(self, substitutions):
        for key, new_value in substitutions.items():
            for arg_index in range(0, len(self.arguments)):
                if self.arguments[arg_index] == key:
                    self.arguments[arg_index] = new_value



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

    def apply_substitutions(self, substitutions):
        for p in self.predicates:
            if isinstance(p, Predicate):
                for arg_index in range(0, len(p.arguments)):
                    for sub in substitutions.keys():
                        # print("arg_index")
                        # print(arg_index)
                        # print("sub")
                        # print(sub)
                        if p.arguments[arg_index] == sub:
                            p.arguments[arg_index] = substitutions[sub]
                            print("Applied subs")
            else:
                p.apply_substitutions(substitutions)

    def get_predicate_name(self):
        predicate_names = []
        for p in self.predicates:
            predicate_names.append(p.get_predicate_name())

        return predicate_names

    def get_matching_predicate_by_name(self, predicate_name, sign=None):
        # print("Self")
        # print(self)
        # print("Self predicates")
        # print(str(self.predicates))
        matched_predicates = []
        for predicate in self.predicates:
            # print("Checking for: " + str(predicate.get_predicate_name()))
            if isinstance(predicate, Predicate):
                # print("Checking for one:" + str(predicate))
                # print("Sign: " + str(sign))
                if predicate.get_predicate_name() == predicate_name and predicate.sign != sign:
                    # print("Matched!")
                    matched_predicates.append(predicate)
            else:
                # print("Checking for list: " + str(predicate.get_predicate_name()))
                matched_predicates += predicate.get_matching_predicate_by_name(predicate_name, sign)

        return matched_predicates

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

    def __init__(self, sentence_string, predicate_list=None):
        if predicate_list is None:
            self.predicate_list = self.get_predicate_list(sentence_string)
            self.sentence_string = sentence_string
        else:
            self.predicate_list = predicate_list
            self.sentence_string = sentence_string

    def apply_substitutions(self, substitutions):
        print("apply_substitutions")
        print(substitutions)
        print("to")
        print(self)
        self.predicate_list.apply_substitutions(substitutions)

    def convert_to_cnf(self, suggestions=None):
        if suggestions is not None and suggestions[0] == "TAKE_NEGATION_INWARD":
            self.negate()

        cnf_check, suggestion = self.is_in_cnf()

        if (
            not cnf_check
            and suggestion == "DISTRIBUTE"
            and self.predicate_list.operator == "|"
        ):
            new_pl_lists = []
            for i in range(0, len(self.predicate_list) - 1):
                p1 = self.predicate_list.predicates[0]
                p2 = self.predicate_list.predicates[i + 1]
                if isinstance(p1, PredicateList) and isinstance(p2, Predicate):
                    for ip in p1.predicates:
                        new_predicate_list = PredicateList([ip, p2], "|")
                        new_pl_lists.append(new_predicate_list)

            new_pl = PredicateList(new_pl_lists, "&")
            self.predicate_list = new_pl

    def is_in_cnf(self):
        p_names = list(flatten(self.predicate_list.get_predicate_name()))
        # print("Checking for")
        # print(self.predicate_list.get_predicate_name())

        suggestions = []
        if len(p_names) == 1:
            return True, []

        if (
            len(p_names) == 2
            and self.predicate_list.operator == "|"
            and self.predicate_list.sign == "P"
        ):
            return True, []

        if self.predicate_list.sign == "N":
            return (False, "TAKE_NEGATION_INWARD")

        sentence_string = str(self)
        if len(p_names) > 2 and "&" not in sentence_string:
            return True, []

        for p in self.predicate_list.predicates:
            if isinstance(p, Predicate) and self.predicate_list.operator == "&":
                return True, []
            if isinstance(p, PredicateList):
                if p.operator == "|":
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


def find_subsitutions(query_predicate, matched_predicate):
    variables = matched_predicate.arguments
    variables = [var.strip() for var in variables]
    substitution = query_predicate.arguments
    substitution = [sub.strip() for sub in substitution]
    substitutions = {}

    print("variables")
    print(variables)
    print("substitution")
    print(substitution)

    if variables == substitution:
        print("variables equal to substitution, return the same")
        for i, v in enumerate(variables):
            substitutions[v] = substitution[i]
        return substitutions        


    for i, v in enumerate(variables):
        if len(v) == 1 and v.islower():
            substitutions[v] = substitution[i]
        elif len(substitution[i]) == 1 and substitution[i].islower():
            substitutions[substitution[i]] = v

    return substitutions


def apply_unit_resolution(predicate_list, predicate_list_2, predicate_to_remove):
    # 1. Combine the two sentences
    # 2. Remove the negated predicates

    print("Apply unit resolution to ")
    print(predicate_list)
    print("And")
    print(predicate_list_2)
    new_sentence_pl = []
    predicate_to_remove.arguments = [var.strip() for var in predicate_to_remove.arguments]

    for p in predicate_list.predicates:
        if isinstance(p, Predicate):
            p.arguments = [var.strip() for var in p.arguments]
            predicate_string = str(p).strip().replace("~", "")
            remove_string = str(predicate_to_remove).strip().replace("~", "")
            # print("predicate_string")
            # print(predicate_string)
            # print("remove_string")
            # print(remove_string)
            if predicate_string == remove_string and p.sign != predicate_to_remove.sign:
                # print("Equal")
                continue
            else:
                # print("Appending")
                # print(p)
                new_sentence_pl.append(p)
        else:
            for ip in p.predicates:
                if isinstance(ip, Predicate):
                    if ip.get_predicate_name() == predicate_to_remove.name:
                        print("Inner Predicates")
                    else:
                        new_sentence_pl.append(ip)
                else:
                    print("Should handle this also fml")




    for p in predicate_list_2.predicates:
        if isinstance(p, Predicate):
            p.arguments = [var.strip() for var in p.arguments]
            predicate_string = str(p).strip().replace("~", "")
            remove_string = str(predicate_to_remove).strip().replace("~", "")
            # print("predicate_string")
            # print(predicate_string)
            # print("remove_string")
            # print(remove_string)
            if predicate_string == remove_string and p.sign == predicate_to_remove.sign:
                # print("Equal")
                continue
            else:
                # print("Appending")
                # print(p)
                new_sentence_pl.append(p)
        else:
            for ip in p.predicates:
                if isinstance(ip, Predicate):
                    if ip.get_predicate_name() == predicate_to_remove.name:
                        print("Inner Predicates")
                    else:
                        new_sentence_pl.append(ip)
                else:
                    print("Should handle this also fml")



    # print("New sentence: ")
    # print(str(new_sentence_pl))
    if len(new_sentence_pl) == 0:
        print("New sentence length is 0")
        return False
    
    new_pl = PredicateList(new_sentence_pl, operator='|')
    sentence_string = str(new_pl).replace("}", "").replace("{", "").replace(" ", "")
    new_sentence = Sentence(sentence_string, new_pl)
    print("New sentence: ")
    print(new_sentence)
    return new_sentence



def apply_resolution(kb, query_sentence, query_predicate):    
    query_predicate_name = query_predicate.name
    print("***************")
    print("Query: " + str(query_predicate))

    for sentence in kb:
        # print("Press any key")
        print("Searching in " + str(sentence))
        # inp = input()
        matched_predicates = sentence.predicate_list.get_matching_predicate_by_name(
            query_predicate_name, query_predicate.sign
        )
        if len(matched_predicates) == 0:
            # print("No matched_predicates in this sentence")
            continue

        for matched_predicate in matched_predicates:
            # Predicate name matched, find substitutions
            # print("query")
            # print(query_predicate)
            print("Found predicate")
            print(matched_predicate)
            # print("substitutions: ")

            substitutions = find_subsitutions(query_predicate, matched_predicate)
            print("substitutions")
            print(substitutions)
            if len(substitutions) == 0:
                print("No substitutions found; Checking for next")
                continue

            # print(substitutions)

            # print("Applying above substitution to sentence: ")
            sentence.apply_substitutions(substitutions)
            query_sentence.apply_substitutions(substitutions)
            print("After applying substitutions: ")
            print(sentence)

            new_sentence = apply_unit_resolution(sentence.predicate_list, query_sentence.predicate_list, query_predicate)
            if not new_sentence:
                print("Reached contractdiction; Exiting resolution")
                return True

            kb.append(new_sentence)

            # return
            for p in new_sentence.predicate_list.predicates:
                if isinstance(p, Predicate):
                    x = apply_resolution(kb, new_sentence, p)
                    if x:
                        return True


file = open("input.txt", "r")
file_lines = file.readlines()
query_string = file_lines[0].strip()
number_of_sentences = int(file_lines[1].strip())

sentences = []

for i in range(2, 2 + number_of_sentences):
    sentences.append(file_lines[i].strip())


knowledge_base = []
for sentence in sentences:
    sentence = sentence.replace(" ", "")
    s = Sentence(sentence)
    # print("For sentence: " + sentence)
    # print(s)
    if "=>" in sentence:
        # print("Removing implication")
        s.remove_implication_sign()
        # print("After removing:")
        # print(s)
    cnf, suggestions = s.is_in_cnf()
    if not cnf:
        # print("Sentence is not in CNF")
        s.convert_to_cnf(suggestions)
        # print("CNF: ")
        # print(s)
        broken_sentences = []
        if s.predicate_list.operator == "&":
            for p in s.predicate_list.predicates:
                # print("Individual predicates: ")
                # print(p)
                sentence_string = (
                    str(p).replace("}", "").replace("{", "").replace(" ", "")
                )
                if isinstance(p, Predicate):
                    predicate_list = PredicateList([p])
                else:
                    predicate_list = p

                new_sentence = Sentence(
                    sentence_string=sentence_string, predicate_list=predicate_list
                )
                # print("New sentence: ")
                # print(new_sentence)
                # print("Inserting to KB")
                knowledge_base.append(new_sentence)
    else:
        # print("Sentence is in CNF")
        knowledge_base.append(s)


main_knowledge_base = copy.deepcopy(knowledge_base)
query_sentence = Sentence(query_string)

query_sentence.negate()
knowledge_base.append(query_sentence)

print("KB:")
for s in knowledge_base:
    print(s)

result = apply_resolution(main_knowledge_base, query_sentence, query_sentence.predicate_list.predicates[0])
print("REsult: ")
print(result)
