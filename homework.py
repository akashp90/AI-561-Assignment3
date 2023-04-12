import re

class Predicate():
    def __init__(self, term_string):
        if term_string[0] == '~':
            self.sign = 'N'
        else:
            self.sign = 'P'
        self.name = term_string.split('(')[0]
        self.name.replace('~', '')
        # This returns '(x, y, z)'; So remove the bracks and get args seperately
        self.arguments = re.findall(r'\(.*?\)', term_string)[0].replace('(', "").replace(")", "").split(',')
        self.term_string = term_string.strip()

    def negate(self):
        self.sign = reverse_sign(self.sign)    
    
    def __str__(self):
        #desc_string = "Name: " + str(self.name) + "; Arguments: " + str(self.arguments) + "; Sign: " + str(self.sign)
        if self.sign == "N":
            sign_string = "~"
        else:
            sign_string = ""
        return sign_string + self.term_string
        #return desc_string

class PredicateListIterator:
   ''' Iterator class '''
   def __init__(self, predicate_list):
       # Team object reference
       self._predicate_list = predicate_list
       # member variable to keep track of current index
       self._index = 0
   def __next__(self):
       ''''Returns the next value from predicate_list object's lists '''
       if self._index < (len(self._predicate_list.predicates)) :
           result = self._predicate_list.predicates[self._index]
           self._index += 1
           return result 
       # End of Iteration
       raise StopIteration

class PredicateList():
    def __init__(self, predicates, operator=None, sign='P'):
        self.predicates = predicates
        self.operator = operator
        self.sign = sign

    def negate(self):
        for p in self.predicates:
            p.negate()

        self.sign = reverse_sign(self.sign)
        if self.operator == "&":
            self.operator = "|"
        elif self.operator == "|":
            self.operator = "&"

    def __str__(self):
        s = ""
        if self.sign == 'N':
            s = '~'

        s = s + '{'
        for p in self.predicates:
                s = s + str(p) + " " + str(self.operator) + " "

        rev = s[::-1]
        rev_op = self.operator[::-1]
        rev = rev.replace(rev_op, "", 1)
        s = rev[::-1]
        s = s + "}"
        return s

    def __add__(self, other):
        return self.predicates + other.predicates

    def __iter__(self):
       ''' Returns the Iterator object '''
       return PredicateListIterator(self)

    def __len__(self):
        return len(self.predicates)

def reverse_sign(sign):
    if sign == "P":
        return "N"
    else:
        return "P"

class Sentence():
    premise = None
    implication = None
    def __init__(self, sentence_string):
        self.predicate_list = self.get_predicate_list(sentence_string)
        self.sentence_string = sentence_string
    
    def negate(self):
        self.predicate_list.negate()

    def remove_implication_sign(self):
        # Remove implication sign
        if self.predicate_list.operator == "=>":
            # a => b == ~a | b
            self.predicate_list.predicates[0].negate()
            self.predicate_list.operator = '|'

    def get_predicate_list(self, sentence_string):
        predicate_terms = []
        predicates = []

        if '=>' in sentence_string:
            premise, conclusion = sentence_string.split('=>')
            if self.is_predicate(premise):
                predicate_terms.append(Predicate(premise))
            else:
                predicate_terms.append(self.get_predicate_list(premise))

            if self.is_predicate(conclusion):
                predicate_terms.append(Predicate(conclusion))
            else:
                x = self.get_predicate_list(conclusion)
                predicate_terms.append(x)

            predicate_list = PredicateList(predicate_terms, '=>')
            return predicate_list

        if '&' in sentence_string:
            anded_terms = sentence_string.split('&')
            for term in anded_terms:
                if self.is_predicate(term):
                    predicate_terms.append(Predicate(term))
                else:
                    predicate_terms.append(self.get_predicate_list(term))


            predicate_list = PredicateList(predicate_terms, '&') 
            return predicate_list

        if '|' in sentence_string:
            ored_terms = sentence_string.split('|')
            for term in ored_terms:
                if self.is_predicate(term):
                    predicate_terms.append(Predicate(term))
                else:
                    predicate_terms.append(self.get_predicate_list(term))


            predicate_list = PredicateList(predicate_terms, '|') 
            return predicate_list

    def is_predicate(self, term):
        if not any([x in term for x in ['&', '|', '=>']]):
            return True
        else:
            return False

    def __str__(self):
        #print("Predicates" + str(type(self.predicates)))
        return str(self.predicate_list) 

file = open("some_input.txt", "r")
file_lines = file.readlines()
query_string = file_lines[0].strip()
number_of_sentences = int(file_lines[1].strip())

sentences = []

for i in range(2, 2 + number_of_sentences):
    sentences.append(file_lines[i].strip())

#print(sentences)
for sentence in sentences:
    s = Sentence(sentence)
    print("For sentence: " + sentence)
    print(s)
    if "=>" in sentence:
        print("Removing implication")
        s.remove_implication_sign()
        print(s)

    if s.predicate_list.operator == "|":
        print("Applying negation")
        s.negate()
        print(s)

