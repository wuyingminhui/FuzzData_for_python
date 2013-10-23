# Build  :  FuzzData 1.0
# Module :  FuzzData
# Auther :  jason.woo(Wu yingmin)
# Blog   :  www.futurehandw.com
# Fuzz the data for web interface testing. Implement the socket API to excute the Fuzz test cases.

import sys
import random
import string
import os
import time
import socket
import re
from UserDict import DictMixin


class odict(DictMixin):

    def __init__(self):
        self._keys = []
        self._data = {}

    def __setitem__(self, key, value):
        if key not in self._data:
            self._keys.append(key)
        self._data[key] = value

    def __getitem__(self, key):
        return self._data[key]

    def __delitem__(self, key):
        del self._data[key]
        self._keys.remove(key)

    def keys(self):
        return list(self._keys)

    def copy(self):
        copyDict = odict()
        copyDict._data = self._data.copy()
        copyDict._keys = self._keys[:]
        return copyDict

class node:
    def __init__(self, id):
        self.id = id
        self.counter = 0
        self.in_ = set()
        self.out = set()
        
    def __str__(self):
        return str(self.__dict__)

def key( items ):
    return "->".join([x.id for x in items])

class pairs_storage:
    def __init__( self, n ):
        self.__n = n
        self.__nodes = {}
        self.__combs_arr = []
        for i in range(n): 
            self.__combs_arr.append( set() )
    
    def add( self, comb ):
        n = len(comb)
        assert(n>0)
        
        self.__combs_arr[n-1].add(key(comb))
        if n == 1 and comb[0].id not in self.__nodes:
            self.__nodes[comb[0].id] = node(comb[0].id)
            return
        
        ids = [x.id for x in comb]
        for i, id in enumerate(ids):
            curr = self.__nodes[id]
            curr.counter += 1
            curr.in_.update( ids[:i] )
            curr.out.update(ids[i+1:])

    def add_sequence( self, seq ):
        for i in range(1, self.__n+1):
            for comb in combinpairs(seq, i):
                self.add(comb)
    
    def get_node_info( self, item ):
        return self.__nodes.get( item.id, node(item.id) )
    
    def get_combs( self ):
        return self.__combs_arr
 
    def __len__( self ):
        return len(self.__combs_arr[-1])

    def count_new_combs( self, seq ):
        s = set([key(z) for z in combinpairs( seq, self.__n)]) - self.__combs_arr[-1]
        return len(s)

class item:
    def __init__(self, id, value):
        self.id        = id
        self.value     = value
        self.weights = []
        
    def __str__(self):
        return str(self.__dict__)

    
def get_comb( arr, n ):
    items = [len(x) for x in arr]
    #print items
    f = lambda x,y:x*y
    total = sum([ reduce(f, z) for z in combinpairs( items, n) ])
    return total
    
    
class pairwise:
    def __iter__( self ):
        return self
        
    def __init__( self, options, filter_func = lambda x: True, previously_tested = [[]], n = 2 ):
        """
        TODO: check that input arrays are:
            - (optional) has no duplicated values inside single array / or compress such values
        """
        
        if len( options ) < 2:
            raise Exception("must provide more than one option")
        for arr in options:
            if not len(arr):
                raise Exception("option arrays must have at least one item")

        self.__filter_func = filter_func
        self.__n = n
        self.__pairs = pairs_storage(n)
        self.__max_unique_pairs_expected = get_comb( options, n )
        self.__working_arr = []

        for i in range( len( options )):
            self.__working_arr.append( [ item("a%iv%i" % (i,j), value) \
                                         for j, value in enumerate(options[i] ) ] )

        for arr in previously_tested:
            if len(arr) == 0:
                continue
            elif len(arr) != len(self.__working_arr):
                raise Exception("previously tested combination is not complete")
            if not self.__filter_func(arr):
                raise Exception("invalid tested combination is provided")
            tested = []
            for i, val in enumerate(arr):
                idxs = [item(node.id, 0) for node in self.__working_arr[i] if node.value == val]
                if len(idxs) != 1:
                    raise Exception("value from previously tested combination is not found in the options or found more than once")
                tested.append(idxs[0])
            self.__pairs.add_sequence(tested)

    def next( self ):
        assert( len(self.__pairs) <= self.__max_unique_pairs_expected )
        p = self.__pairs
        if len(self.__pairs) == self.__max_unique_pairs_expected:
            # no reasons to search further - all pairs are found
            raise StopIteration
        
        previous_unique_pairs_count= len(self.__pairs)
        chosen_values_arr          = [None] * len(self.__working_arr)
        indexes                    = [None] * len(self.__working_arr)
        
        direction = 1
        i = 0
        
        while -1 < i < len(self.__working_arr):
            if direction == 1: # move forward
                self.resort_working_array( chosen_values_arr[:i], i )
                indexes[i] = 0
            elif direction == 0 or direction == -1: # scan current array or go back
                indexes[i] += 1
                if indexes[i] >= len( self.__working_arr[i] ):
                    direction = -1
                    if i == 0:
                        raise StopIteration
                    i += direction    
                    continue
                direction = 0
            else:
                raise Exception("next(): unknown 'direction' code.")
                    
            chosen_values_arr[i] =  self.__working_arr[i][ indexes[i] ]
            
            if self.__filter_func( self.get_values_array( chosen_values_arr[:i+1] ) ):
                assert(direction > -1)
                direction = 1
            else:
                direction = 0
            i += direction    
        
        if  len( self.__working_arr ) != len(chosen_values_arr):
            raise StopIteration
        
        self.__pairs.add_sequence( chosen_values_arr )

        if len(self.__pairs) == previous_unique_pairs_count:
            # could not find new unique pairs - stop
            raise StopIteration
        
        # replace returned array elements with real values and return it
        return self.get_values_array( chosen_values_arr )
        
    def get_values_array( self, arr ):
        return [ item.value for item in arr ]
    
    def resort_working_array( self, chosen_values_arr, num ):
        for item in self.__working_arr[num]:
            data_node = self.__pairs.get_node_info( item )
            
            new_combs = []
            for i in range(0, self.__n):
                # numbers of new combinations to be created if this item is appended to array
                new_combs.append( set([key(z) for z in combinpairs( chosen_values_arr+[item], i+1)]) - self.__pairs.get_combs()[i] )
            # weighting the node
            item.weights =  [ -len(new_combs[-1]) ]    # node that creates most of new pairs is the best
            item.weights += [ len(data_node.out) ] # less used outbound connections most likely to produce more new pairs while search continues
            item.weights += [ len(x) for x in reversed(new_combs[:-1])]
            item.weights += [ -data_node.counter ]  # less used node is better
            item.weights += [ -len(data_node.in_) ] # otherwise we will prefer node with most of free inbound connections; somehow it works out better ;)
            
        self.__working_arr[num].sort( lambda a,b: cmp(a.weights, b.weights) )

    # statistics, internal stuff        
    def get_pairs_found( self ):
        return self.__pairs
    
def combinpairs(items, n):
    if n==0: yield []
    else:
        for i in xrange(len(items)):
            for cc in combinpairs( items[i+1:], n-1) :
                yield [items[i]]+cc

class FuzzParserError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return "please set the valname first"


class FuzzParser:
  """Main class - should be imported into fuzzer scripts."""
  def __init__(self):
    """Constructor that is called when the class is instantiated."""
    self.objectList = odict()
    self.extraList = []
    self.rawList = []
    self.valList = []
    self.resultList = []
    self.exportList = []
    self.TEMList = []
    self.valconnect = "&"
    self.version = "Fuzzdata-1.0"
    self.illegalList = ["'", '"', "\\", "//", "#", "!", "~", "@", "^", "%", "&", "*", "&", "_"
                        "add", "delete", "remove", "modify" ,"get", "post", "put", "||", "--"
                        "or", "and", "&&" , "|", "<", ">", "?", ",", "%20" , "==", ":", ";",
                        "=", "' or 'a' = a","<script>alert('XSS')</script>","<IMG SRC='javascript:alert(1);'>"
                        ]

  def append(self, item):
    """Append data to the Fuzzparser."""
    self.rawList.append(item)
    
  def delete(self, item):
    """Remove data by name from the Fuzzparser."""
    del self.objectList[str(item.getvalname())]

  def display(self):
    """Prints all of the objects in the Fuzzparser."""
    for key in self.objectList:
      print 'key=%s, value=%s' % (key, self.objectList[key])

  def version(self):
    """Prints the version."""
    print self.version

  def auto(self):
    options = []
    resultlist = [] 
    self.permute()
    options = self.__extractPlayload()
    finallist = pairwise(options)
    resultlist = self.result(finallist)
    for i, v in enumerate(resultlist):
        print "%i:\t%s" % (i, str(v))
    return resultlist

   
  def exportToCSV(self):
      valname = []
      filename = ""
      for j in self.valList:
          valname.append(j)
      filename = "-".join(list(valname))
      filename = filename + ".csv"
      file_object = open(filename, 'wb')
      file_object.write((",".join(list(valname)))+"\n")
      file_object.close

      file_object1 = open(filename, 'w+')    
      for singlecase in self.exportList:
          file_object1.write((",".join(list(singlecase)))+"\n")      
      file_object1.close         

  def result(self , rlist):
    for value in rlist:
      resultstring = []
      resultstring1 = []
      exportList = []
      string1 = str(self.valconnect)
      result = ""
      result1 = ""
      result2 = ""
      exportresult = ""
      for i in xrange(len(value)):
          resultstring.append(str(self.valList[i]) + str(self.extraList[i]) + repr(value[i]).strip('\''))
          exportList.append(str(value[i]))
      result = string1.join(list(resultstring))
      choices = True, False,
      if random.choice(choices):
          for i in xrange(len(value)):
              resultstring1.append(str(self.valList[i]) + str(self.extraList[i]) + str(value[i])+ repr(self.TEMList[i]).strip('\''))
              exportList.append(str(value[i]))
          result2 = string1.join(list(resultstring1))
          random.shuffle(resultstring)
          result1 = string1.join(list(resultstring))
          self.resultList.append(result1 + repr(self.TEMList[i]).strip('\''))
          self.resultList.append(result2 + repr(self.TEMList[i]).strip('\''))
      self.exportList.append(exportList)
      self.resultList.append(result + repr(self.TEMList[i]).strip('\''))
    return self.resultList
    
  def __extractPlayload(self):
    self.playlist = []
    for key in self.objectList:
      self.playlist.append(self.objectList[key])
      self.valList.append(key)
    return self.playlist

  def getvalconnect(self):
    """Returns the payload of the current permutation."""
    return self.valconnect

  def setvalconnect(self, valconnect):
    self.valconnect = valconnect

  def displayModes(self):
    """Display a list of supported modes for Fuzzparser.permute()."""
    print "The following modes are available:"
    for item in self.modes:
      print item

  def getDebug(self):
    """Returns the debugging status."""
    return self.debug

  def setDebug(self, debug):
    """Sets the debugging status to True or False.  Defaults to False.""" 
    self.debug = debug

  def getGlobalDebug(self):
    """Returns the global debugging status."""

  def setGlobalDebug(self, debug):
    """Sets the debugging status to True or False for all data objects in the Fuzzparser.  Defaults to False."""
    if debug is True:
      for item in self.objectList:
        item.setDebug(True)
    if debug is False:
      for item in self.objectList:
        item.setDebug(False)
    self.setDebug(debug)

  def getRandomstr(self, n):
    st = ''
    for i in range(n+1):
      st = st.join(['',chr(0+random.randint(0,255))])
    return st


  def permute(self):
    """Creates a random permutation of the content for each data object in the Fuzzparser."""
    for item in self.rawList:
      if isinstance(item, BoneString):
        if str(item.getvalname()) == ""  :
          raise FuzzParserError(1)
        tempList = [] # list to build string
        randomString = "" 
        size = 0
        if item.getMinSize() == item.getMaxSize():
          size = item.getMinSize()
        else:
          size = random.randrange(item.getMinSize(), item.getMaxSize())

        #Fuzz string data
        tempList.append("")
        tempList.append(self.getRandomstr(item.getMaxSize()))
        tempList.append(self.getRandomstr(item.getMaxSize()+100))
        tempList.append(self.getRandomstr(size))
        tempList.append(item.getContent())
        tempList.append(self.getRandomstr(len(item.getContent())))
        tempList.append(item.getIllegalChars())
        if item.getMode().lower() == "random":
          for i in xrange(size):
            randomString = string.join(random.choice(item.charRange), '')
          tempList.append(randomString)
          tempList.extend(random.sample(self.illegalList, int(len(self.illegalList)*0.6)))
        if item.getMode().lower() == "increment":
          for i in xrange(int((item.getMaxSize()-item.getMinSize())*0.8)):
            for i in xrange((int((item.getMaxSize()-item.getMinSize())*0.8))):
              randomString = string.join(random.choice(item.charRange), '')
            tempList.append(randomString)
            tempList.extend(random.sample(self.illegalList, int(len(self.illegalList)*0.8)))
        if item.getMode().lower() == "full":
          tempList.extend(self.illegalList)
          for i in xrange(int(item.getMaxSize()-item.getMinSize())):
            for i in xrange((int(item.getMaxSize()-item.getMinSize()))):
              randomString = string.join(random.choice(item.charRange), '')
            tempList.append(randomString)
        tempList = list(set(tempList))
        self.objectList[str(item.getvalname())] =  tempList
       # print item.getvalname()
        self.extraList.append(item.getConnector())
        self.TEMList.append(item.getTerminator())
        #self.valList.append(item.getvalname())
        continue

      #Fuzz char data
      elif (isinstance(item, BoneChar)):
        if str(item.getvalname()) == ""  :
          raise FuzzParserError(1)
        number = 0
        tempList1 = []  
        if item.getMinSize() == item.getMaxSize():
          number = item.getMinSize()
        else:
          number = random.randrange(item.getMinSize(), item.getMaxSize())
        tempList1.append("")
        tempList1.append(item.getContent())
        tempList1.append(random.choice(item.charRange))
        tempList1 = list(set(tempList1))
        self.objectList[str(item.getvalname())] =  tempList1
       # print item.getvalname()
        self.extraList.append(item.getConnector())
        self.TEMList.append(item.getTerminator())
        #self.valList.append(item.getvalname())
        continue

      #Fuzz Integer,LongInt data
      elif ( isinstance(item, BoneInteger) or isinstance(item, BoneLongInt)):
        if str(item.getvalname()) == ""  :
          raise FuzzParserError(1) 
        number = 0
        tempList2 = []
        list1 = []
        if item.getMinSize() == item.getMaxSize():
          number = item.getMinSize()
        else:
          number = random.randrange(item.getMinSize(), item.getMaxSize())
        tempList2.append("")
        tempList2.append(item.getContent())
        tempList2.append(item.getMinSize() - 1)
        tempList2.append(item.getMinSize())
        tempList2.append(item.getMaxSize() + 1)
        tempList2.append(item.getMaxSize())
        if item.getMode().lower() == "random":
          tempList2.append(number)
        if item.getMode().lower() == "increment":
          for i in xrange(int((item.getMaxSize()-item.getMinSize()))):
            list1.append(i)
          tempList2.extend(random.sample(list1,int((item.getMaxSize()-item.getMinSize())*0.8)) ) 
          tempList2.append(self.getRandomstr(0))
        if item.getMode().lower() == "full":
          for i in xrange(int((item.getMaxSize()-item.getMinSize()))):
            number = i+(int(item.getMinSize()))
            tempList2.append(number)
            choices = True, False,
            if random.choice(choices):
              tempList2.append(self.getRandomstr(0))
        tempList2 = list(set(tempList2))
        self.objectList[str(item.getvalname())] =  tempList2
       # print item.getvalname()
        self.extraList.append(item.getConnector())
        self.TEMList.append(item.getTerminator())
        #self.valList.append(item.getvalname())
        continue

      #Fuzz Float data
      elif (isinstance(item, BoneFloat)):
        if str(item.getvalname()) == ""  :
          raise FuzzParserError(1) 
        number = 0
        tempList3 = []
        if item.getMinSize() == item.getMaxSize():
          number = item.getMinSize()
        else:
          number = random.randrange(item.getMinSize(), item.getMaxSize())
        tempList3.append("")
        tempList3.append(item.getContent())
        tempList3.append(item.getMinSize() - 1 + random.random())
        tempList3.append(item.getMinSize() + random.random())
        tempList3.append(item.getMaxSize() + 1 + random.random())
        tempList3.append(number+random.random() + random.random())
        tempList3.append(item.getMaxSize())
        tempList3 = list(set(tempList3))
        if item.getMode().lower() == "random":
          tempList3.append(random.uniform(item.getMinSize(),item.getMaxSize()))
        if item.getMode().lower() == "increment":
          for i in xrange((int((item.getMaxSize()-item.getMinSize())*0.8))):
            tempList3.append(random.uniform(item.getMinSize(),item.getMaxSize()))
          tempList2.append(self.getRandomstr(0))
        if item.getMode().lower() == "full":
          for i in xrange((int(item.getMaxSize()-item.getMinSize()))):
            tempList3.append(random.uniform(item.getMinSize(),item.getMaxSize()))
            choices = True, False,
            if random.choice(choices):
              tempList2.append(self.getRandomstr(0))
        self.objectList[str(item.getvalname())] =  tempList3
       # print item.getvalname()
        self.extraList.append(item.getConnector())
        self.TEMList.append(item.getTerminator())
        #self.valList.append(item.getvalname())
        continue

class FuzzObject:
  def __init__(self):
    """Constructor that is called when the class is instantiated."""
    # set defaults
    self.valname = ""
    self.minsize = 1
    self.maxsize = 10
    self.debug = False
    self.optional = False
    self.content = ""
    self.byteorder = None
    self.mode = "random"
    self.connector = "="
    self.terminator = ""

  def getConnector(self):
    return self.connector

  def setConnector(self, connector):
    self.connector = connector

  def getMode(self):
    return self.mode

  def setMode(self, mode):
    self.mode = mode

  def getvalname(self):
    return self.valname

  def setvalname(self, valname):
    self.valname = valname

  def getMinSize(self):
    #Returns the minsize property of the data object.
    return self.minsize

  def setMinSize(self, minsize):
    """Sets the minsize property of the data object to an integer."""
    if self.debug:
      print "++ Setting minsize for %s to: %s ++" % (str(self), minsize)
    self.minsize = minsize

  def getMaxSize(self):
    """Gets the maxsize property of the data object."""
    return self.maxsize

  def setMaxSize(self, maxsize):
    """Sets the maxsize property of the data object to an integer."""
    if self.debug:
      print "++ Setting maxsize for %s to: %s ++" % (str(self), maxsize)
    self.maxsize =  maxsize

  def display(self):
    """Print the data object."""
    print "Data Object: %s" % str(self)
    stringrep = str(self.__dict__.items()) 
    print stringrep + "\n"

  def getContent(self):
    """Returns the content of the data object."""
    return self.content

  def setContent(self, content):
    """Sets the content of the data object."""
    self.content = content

  def getTerminator(self):
    """Returns a terminator string."""
    return self.terminator

  def setTerminator(self, terminator):
    """Sets a terminator string for the data object."""
    if self.debug:
      print "++ Setting terminator characters for %s to: %s ++" % (str(self), terminator)
    self.terminator = terminator
    
class BoneInteger(FuzzObject):
  #Integer represents the Integer(short) data type."""
  def __init__(self):
    FuzzObject.__init__(self)
    self.content = 0
    #default
    self.signed = False
    self.minsize = 0
    self.maxsize = 2**16-1
    self.connector = "="

  def getSigned(self):
    #Returns the value of the signed field for the data object.
    return self.signed

  def setSigned(self, signed):
	#Sets the value of the signed field for the data object.
    if self.debug:
      print "+++ Setting signed value for %s to: %s" % (str(self), signed)
    self.signed = signed
    if self.signed:
      self.setMinSize(-2**15)
      self.setMaxSize(2**15-1)
    else:
      self.setMinSize(0)
      self.setMaxsize(2**16)
  
class BoneLongInt(FuzzObject):
  #Long for the long data type.
  def __init__(self):
    FuzzObject.__init__(self)
    self.content = 0L
    #default
    self.signed = False
    self.minsize = 0
    self.maxsize = 2**32-1
    self.connector = "="

  def getSigned(self):
    return self.signed

  def setSigned(self, signed):
    if self.debug:
      print "Setting signed value for %s to: %s" % (str(self), signed)
    self.signed = signed
    if self.signed:
      self.setMinSize(-2**31)
      self.setMaxSize(2**31-1)
    else:
      self.setMinSize(0)
      self.setMaxSize(2**32-1)

class BoneFloat(FuzzObject):
  #Long for the long data type.
  def __init__(self):
    FuzzObject.__init__(self)
    self.content = float(0)
    self.connector = "="
    #default
    self.signed = False
    self.minsize = float((-2**32)+0.123456789123456)
    self.maxsize = float((2**32-1)+0.123456789123456)

	  
class BoneChar(FuzzObject):
  #Char represents the char data type.
  def __init__(self):
    FuzzObject.__init__(self)
    self.content = 0
    # default
    self.signed = False
    self.minsize = 0
    self.maxsize =  2**8-1
    self.connector = "="

  def getSigned(self):
    return self.signed

  def setSigned(self, signed):
    if self.debug:
      print "+++ Setting signed value for %s to: %s" % (str(self), signed)
    self.signed = signed

    if self.signed:
      self.setMinSize(-2**7)
      self.setMaxSize(2**7-1)
    else:
      self.setMinSize(0)
      self.setMaxSize(2**8)
	  
class BoneString(FuzzObject):
  """BoneString represents a freeform string."""
  def __init__(self):
    FuzzObject.__init__(self)
    self.illegalchars = ""
    self.charRange = []
    self.terminator = None
    self.__extractCharRange()
    self.valname = ""
    self.connector = "="

  def __extractCharRange(self):
    charTable = ""
    tempRange = ""                 
    charTable = string.maketrans('', '')
    self.charRange = list(string.translate(charTable, charTable, self.illegalchars))

  def getIllegalChars(self):
    """Returns a list of illegal characters."""
    return self.illegalchars

  def setIllegalChars(self, chars):
    """Sets a string of illegal characters."""
    if self.debug:
      print "++ Setting illegal character range for %s to: %s ++" % (str(self), chars)
    self.illegalchars = chars
    self.__extractCharRange()

  def getContentSize(self):
    """Returns the length of the current content."""
    return len(self.content)

	
class Assert:
  """Assert is a class for testing assert, for test use with the FuzzData
  """
  def assertEqual(self, origdata ,distdata):
      if(cmp(str(origdata).lower(), str(distdata).lower()) == 0):
          return "PASS"
      else:
          return "False"
		
  def assertNotEqual(self, origdata ,distdata):
      if(cmp(str(origdata).lower(), str(distdata).lower())):
          return "False"
      else:
          return "PASS"
		
  def assertContain(self, data ,containdata):
      contain_re = re.compile(str(containdata),
                      re.MULTILINE | re.DOTALL | re.IGNORECASE)
      match = contain_re.search(str(data))
      if match:
          return "PASS"
      else:
          return "False"

  def assertNotContain(self, data ,containdata):
      contain_re = re.compile(str(containdata),
                      re.MULTILINE | re.DOTALL | re.IGNORECASE)
      match = contain_re.search(str(data))
      if match:
          return "False"
      else:
          return "PASS"

class FuzzSocket(Assert):
  """FuzzSocket is a wrapper class for the Python socket API, for specialized use with the FuzzData
  """

  def __init__(self):
    self.host = 'localhost'
    self.port = 80
    self.recList = {}
    self.assertstring = ''
    self.assertcontain = ''
	
  def exportToCSV(self , reclist):
      """export to csv file
      """
      filename = time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time()))+ "-result.csv"
      file_object = open(filename, 'wb')
      list1 = ["host","port","Parameter","result","F or P"]
      file_object.write((",".join(list1))+"\n")
      
      for result in reclist:
          c = reclist[result].split("!@result@!")
          singleresult = [str(self.host), str(self.port), repr(result) ,c[0], c[1] ]
          file_object.write((",".join(list(singleresult)))+"\n")      
      file_object.close      

  def PlaySocket(self, type, playload ,size, sleeptime):
    """Main step to initializes a socket of the specified type, either 'udp' or 'tcp'."""
    self.type = type
    self.TCPok = True
    if self.type == 'udp':
      try:
          sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
          self.sleep(sleeptime)
          sock.sendto(playload, (self.host, self.port))
          data = sock.recv(size)
      except socket.error, msg:
          print "Parameter : "+ playload
          self.recList[playload] = "Could not connect...!@result@!False"
          print msg
          self.TCPok = False
      if self.TCPok:
          print "Parameter : "+ playload
          print "Response  : "+ data
          self.recList[playload] = data[:-1]
          if(self.assertstring != '' and self.assertstring != None):
              self.recList[playload] = data[:-1] + '!@result@!' +self.assertEqual(data,self.assertstring)
          if(self.assertcontain != '' and self.assertcontain != None):
              self.recList[playload] = data[:-1] + '!@result@!' +self.assertContain(data,self.assertcontain)
          sock.close()
    else:
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      try:
          sock.connect((self.host, self.port))
      except socket.error, msg:
          print "Could not connect: ", msg
          self.recList[playload] = "Could not connect...!@result@!False"
      try:
          self.sleep(sleeptime)
          sock.send(playload)
          data = sock.recv(size)
      except socket.error, msg:
          print "Parameter : "+ playload
          self.recList[playload] = "Could not connect...!@result@!False"
          self.TCPok = False
      if self.TCPok:
          print "Parameter : "+ playload
          print "Response  : "+ data
          self.recList[playload] = data[:-1]
          if(self.assertstring != '' and self.assertstring != None):
              print data + '!@result@!' +self.assertEqual(data,self.assertstring)
              self.recList[playload] = data[:-1] + '!@result@!' +self.assertEqual(data,self.assertstring)
          if(self.assertcontain != '' and self.assertcontain != None):
              print data + '!@result@!' +self.assertContain(data,self.assertcontain)
              self.recList[playload] = data[:-1] + '!@result@!' +self.assertContain(data,self.assertcontain)
              
          sock.close()

  def setHostPort(self ,host, port):
      self.host = host
      self.port = port

  def getHost(self):
      return self.host

  def getPort(self):
      return self.port  

  def setAssertstring(self, assertstring):
      self.assertstring = assertstring

  def getAssertstring(self):
      return self.assertstring 
	  
  def setAssertcontain(self, assertcontain):
      self.assertcontain = assertcontain

  def getAssertcontain(self):
      return self.assertcontain 

  def sleep(self, secs):
    """Alias for time.sleep, sleeps for the number of seconds specified by the secs argument."""
    time.sleep(secs)

  def close(self , sock):
    """Alias for socket.close method.  This closes the existing socket."""
    sock.close()

  def playTCPFuzz(self , tcplist , size ,sleeptime):
      """Alias for loop to deal with the single tcp request.  This closes the existing socket."""
      for msg in tcplist:
          self.PlaySocket("tcp", msg, 4096, 1)
          self.sleep(sleeptime)
      return self.recList

  def playUDPFuzz(self , udplist , size ,sleeptime):
      """Alias for loop to deal with the single udp request.  This closes the existing socket."""
      for msg in udplist:
          print self.recList
          self.PlaySocket("udp", msg, 4096, 1)
          self.sleep(sleeptime)
      return self.recList

