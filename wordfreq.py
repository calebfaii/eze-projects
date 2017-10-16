from operator import itemgetter
import string
from termcolor import colored
import random

class wordContainer(object):

    wordList = []

    lengthList = []
    lenListIsAsc = False
    lenListIsDesc = False

    frequencyDict = {}

    frequencyList = []
    freqListIsAsc = False
    freqListIsDesc = False

    def __init__(self):

        try:
            self.loadNames()
        except Exception, e:
            print "Failed to load words: %s" % e

        try:
            self.countFrequency()
            self.createList()
            self.getLengths()
        except Exception, e:
            print "Failed to process words: %s" % e
        self.runAllCalcs()

    # Helper init functions:

    def loadNames(self, filename='hab.txt'):

        with open(filename) as text:
            for line in text:
                line = line.translate(None, string.punctuation)
                line = "".join(char for char in line if ord(char)<128)
                for word in line.strip('\n').split(' '):
                    if len(word) > 0:
                        self.wordList.append(word)

    def countFrequency(self):

        for word in self.wordList:
            if word in self.frequencyDict.keys():
                currentCount = self.frequencyDict.get(word)
                newCount = currentCount + 1
                self.frequencyDict[word] = newCount
            if word not in self.frequencyDict.keys():
                self.frequencyDict.update({word: 1})

    def createList(self):

        for key in self.frequencyDict.keys():
            pair = [key, self.frequencyDict.get(key)]
            self.frequencyList.append(pair)

    def getLengths(self):

        for key in self.frequencyDict.keys():
            length = len(key)
            self.lengthList.append([key, length])

    def printDivider(self):

        divider = colored("----------------------------------------------", 'grey', attrs=['bold'])
        print divider

    def printList(self, data):

        for x in data:
            print x[0], " - ", x[1]

    def printTuple(self, data):

        for x in data:
            print x[0], " - ", x[1]

    def printString(self, data):

        print data

    def printResult(self, id, data):

        printMethods = {list: self.printList, tuple: self.printTuple, str: self.printString}
        self.printDivider()
        id = self.randomColorizer(id)
        self.printString(id)
        self.printString('\n')
        dataType = type(data)


        try:
            printMethods[dataType](data)
        except KeyError, k:
            try:
                print(data)
            except Exception, e:
                print "Error: print failed. %s" % e

    def randomColorizer(self, item):

        colors = ['red', 'green', 'yellow', 'magenta', 'cyan', 'grey']
        thiscolor = random.choice(colors)
        return colored(item, thiscolor)



    # Counting and sorting operations:

    def firstPassStats(self):

        id = "Preliminary dataset analysis"

        total = "Number of total words: %d" % len(self.wordList)
        unique = "Number of unique words: %d" % len(self.frequencyDict.keys())
        response = total + '\n' + unique
        self.printResult(id, response)

    def sortFreqListAsc(self):

        sortedAsc = sorted(self.frequencyList, key=itemgetter(1), reverse=True)
        self.frequencyList = sortedAsc
        self.freqListIsAsc = True
        self.freqListIsDesc = False

    def sortLenListAsc(self):

        sortedAsc = sorted(self.lengthList, key=itemgetter(1), reverse=True)
        self.lengthList = sortedAsc
        self.lenListIsAsc = True
        self.lenListIsDesc = False

    def topTenWords(self):

        id = "Top ten words occurring most frequently:"

        if not self.freqListIsAsc:
            self.sortFreqListAsc()

        generator = [[self.frequencyList[i][0], self.frequencyList[i][1]] for i in range(0, 10)]
        self.printResult(id, generator)

    def longestWord(self):

        id = "Longest word:"

        if not self.lenListIsAsc:
            self.sortLenListAsc()

        phrase = "%s - %d characters" % (self.lengthList[0][0], self.lengthList[0][1])
        self.printResult(id, phrase)

    def wordsOnce(self):

        id = "Number of words occurring only once:"

        counter = 0
        for i in self.frequencyList:
            if i[1] == 1:
                counter += 1
        self.printResult(id, counter)

    def makeRandomSentence(self):

        id = "Here's a sentence, of random length, containing random words from this set:"

        length = random.randrange(4, 15)

        sentence = ''
        while length > 0:
            sentence += random.choice(self.wordList)
            if length > 1:
                sentence += ' '
            length -= 1
        sentence += '.'
        sentence = self.randomColorizer(sentence)
        self.printResult(id, sentence)

    def getAllWordScores(self):

        x = raw_input("Print all words? This may take a while.\nY to print, N to cancel.")

        if x == 'N':
            return

        id = "All words, descending order of occurrences:"

        if not self.freqListIsAsc:
            self.sortFreqListAsc()
        generator = [[i[0], i[1]] for i in self.frequencyList]
        self.printResult(id, generator)

    def runAllCalcs(self):

        self.firstPassStats()
        self.topTenWords()
        self.longestWord()
        self.wordsOnce()
        self.makeRandomSentence()
        self.getAllWordScores()

instance = wordContainer()
