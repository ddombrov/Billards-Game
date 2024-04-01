CC = clang
CFLAGS = -Wall -std=c99 -pedantic
PYTHONVER = python3.11

all: _phylib.so

libphylib.so: phylib.o
	$(CC) phylib.o -shared -lm -o libphylib.so

phylib.o: phylib.c phylib.h
	$(CC) $(CFLAGS) -c phylib.c -fPIC -o phylib.o

phylib_wrap.c phylib.py: phylib.i libphylib.so
	swig -python phylib.i

phylib_wrap.o: phylib_wrap.c
	$(CC) $(CFLAGS) -c phylib_wrap.c -I/usr/include/$(PYTHONVER)/ -fPIC -o phylib_wrap.o

_phylib.so: phylib_wrap.o
	$(CC) $(CFLAGS) -shared phylib_wrap.o -L. -L/usr/lib/$(PYTHONVER) -l$(PYTHONVER) -lphylib -o _phylib.so

A2test1: A2Test1.py _phylib.so 
	 export LD_LIBRARY_PATH=`pwd` && python3 A2Test1.py

A2test2: A2Test2.py _phylib.so 
	 export LD_LIBRARY_PATH=`pwd` && python3 A2Test2.py

 test1: A3Test1.py _phylib.so 
 	 export LD_LIBRARY_PATH=`pwd` && python3 A3Test1.py

 test2: A3Test2.py _phylib.so 
 	 export LD_LIBRARY_PATH=`pwd` && python3 A3Test2.py

 test3: A3Test3.py _phylib.so 
 	 export LD_LIBRARY_PATH=`pwd` && python3 A3Test3.py

 test4: A3Test4.py _phylib.so 
 	 export LD_LIBRARY_PATH=`pwd` && python3 A3Test4.py

 test5: A3Test5.py _phylib.so 
 	 export LD_LIBRARY_PATH=`pwd` && python3 A3Test5.py

testPort: server.py _phylib.so 
	 export LD_LIBRARY_PATH=`pwd` && python3 server.py 3000

clean:
	rm -f *.o *.so
