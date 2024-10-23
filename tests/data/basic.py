from drafter import *
from dataclasses import dataclass


@dataclass
class A:
    field1: int
    field2: str
    
@dataclass
class C:
    xxx: int
    yyy: str

@dataclass
class B:
    a: A
    field3: float
    list_of_c: list[C]

@route
def first_page(b: B):
    Button('Submit', second_page)
    Link('Another', 'fourth_page')
    b.a.field1 += 1
    another_func()
    
@route
def second_page(b: B):
    return None
    
@route
def third_page(b: B):
    return None
    
@route
def fourth_page(b: B):
    b.a.field2 = 'new value'
    return third_page(b)

def my_helper():
    return "helper"

def another_func():
    pass

start_server(B(field3=3.14, a=A(1, 'hello'), list_of_c=[C(1, 'one'), C(2, 'two')]))