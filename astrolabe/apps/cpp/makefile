LIB = ../../lib/cpp
CXXFLAGS = -Wall -I../../lib/cpp -O
objects = \
	$(LIB)/calendar.o \
	$(LIB)/dicts.o \
	$(LIB)/dynamical.o \
    $(LIB)/elp2000.o \
    $(LIB)/equinox.o \
    $(LIB)/globals.o \
    $(LIB)/nutation.o \
    $(LIB)/riseset.o \
    $(LIB)/sun.o \
    $(LIB)/util.o \
    $(LIB)/vsop87d.o
    
apps = \
    check_equinox \
    check_vsop87d \
    create_text_vsop_db \
    cronus \
    solstice \
    time_vsop_db_loads \
    validate_meeus 

check_vsop87d : check_vsop87d.o 
check_equinox : check_equinox.o
create_text_vsop_db : create_text_vsop_db.o
cronus : cronus.o
solstice : solstice.o
time_vsop_db_loads : time_vsop_db_loads.o
validate_meeus : validate_meeus.o

$(objects) : $(LIB)/astrolabe.hpp

$(apps) : $(LIB)/astrolabe.a($(objects)) $(LIB)/astrolabe.hpp
	g++ -o $@ $@.o -Wall -O -I$(LIB) $(LIB)/astrolabe.a

.PHONY : all
all : $(apps)

