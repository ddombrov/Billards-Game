CC = clang
CFLAGS = -Wall -std=c99 -pedantic
PYTHONVER = python3.9

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

#  test1: A4Test1.py _phylib.so 
#  	export LD_LIBRARY_PATH=`pwd` && python3 A4Test1.py

#  test2: A4Test2.py _phylib.so 
#  	export LD_LIBRARY_PATH=`pwd` && python3 A4Test2.py

#  test3: A4Test3.py _phylib.so 
#  	export LD_LIBRARY_PATH=`pwd` && python3 A4Test3.py

#  test4: A4Test4.py _phylib.so 
#  	export LD_LIBRARY_PATH=`pwd` && python3 A4Test4.py

clean:
	rm -f *.o *.so
