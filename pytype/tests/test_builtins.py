"""Tests of builtins (in pytd/builtins/__builtins__.pytd)."""

import unittest
from pytype.tests import test_inference


class BuiltinTests(test_inference.InferenceTest):

  def testRepr1(self):
    with self.Infer("""
      def t_testRepr1(x):
        return repr(x)
      t_testRepr1(4)
    """, deep=False, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        def t_testRepr1(x: int) -> str
      """)

  def testRepr2(self):
    with self.Infer("""
      def t_testRepr2(x):
        return repr(x)
      t_testRepr2(4)
      t_testRepr2(1.234)
      t_testRepr2('abc')
    """, deep=False, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        def t_testRepr2(x: float or int or str) -> str
      """)

  def testRepr3(self):
    with self.Infer("""
      def t_testRepr3(x):
        return repr(x)
      t_testRepr3(__any_object__())
    """, deep=False, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        def t_testRepr3(x) -> str
      """)

  def testEvalSolve(self):
    with self.Infer("""
      def t_testEval(x):
        return eval(x)
      t_testEval(4)
    """, deep=False, solve_unknowns=True, extract_locals=True) as ty:
      # TODO(kramm): https://review/#review/87297298/pytype/tests/test_builtins.py&v=s11&l=37F
      self.assertTypesMatchPytd(ty, """
        # TODO(pludemann): should this return `?` instead of `object`?
        def t_testEval(x: int) -> ?
      """)

  def testIsinstance1(self):
    with self.Infer("""
      def t_testIsinstance1(x):
        # TODO: if isinstance(x, int): return "abc" else: return None
        return isinstance(x, int)
    """, deep=True, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        def t_testIsinstance1(x: object) -> bool
      """)

  @unittest.skip("Broken - needs more sophisticated booleans")
  def testIsinstance2(self):
    with self.Infer("""
      def t_testIsinstance2(x):
        assert isinstance(x, int)
    """, deep=True, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        # TODO(pludemann): currently does (x: object)
        def t_testIsinstance2(x: int) -> NoneType
      """)

  def testPow1(self):
    with self.Infer("""
      def t_testPow1():
        # pow(int, int) returns int, or float if the exponent is negative, or
        # long if the result is larger than an int. Hence, it's a handy function
        # for testing UnionType returns.
        return pow(1, -2)
    """, deep=True, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        def t_testPow1() -> float or int or long
      """)

  def testPow2(self):
    with self.Infer("""
      def t_testPow2(x, y):
        # pow(int, int) returns int, or float if the exponent is negative, or
        # long if the result is larger than an int. Hence, it's a handy function
        # for testing UnionType returns.
        return pow(x, y)
    """, deep=True, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        def t_testPow2(x: bool or complex or float or int or long, y: bool or complex or float or int or long) -> bool or complex or float or int or long
      """)

  def testMax1(self):
    with self.Infer("""
      def t_testMax1():
        # max is a parameterized function
        return max(1, 2)
    """, deep=True, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        def t_testMax1() -> int
        """)

  def testMax2(self):
    # TODO(kramm): This test takes over six seconds
    with self.Infer("""
      def t_testMax2(x, y):
        # max is a parameterized function
        return max(x, y)
    """, deep=True, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        def t_testMax2(x: object, y: object) -> ?
        """)

  def testDict(self):
    with self.Infer("""
      def t_testDict():
        d = {}
        d['a'] = 3
        d[3j] = 1.0
        return _i1_(_i2_(d).values())[0]
      def _i1_(x):
        return x
      def _i2_(x):
        return x
      t_testDict()
    """, deep=False, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        def t_testDict() -> float or int
        # _i1_, _i2_ capture the more precise definitions of the ~dict, ~list
        def _i1_(x: list<float or int>) -> list<float or int>
        def _i2_(x: dict<complex or str, float or int>) -> dict<complex or str, float or int>
        # TODO(pludemann): solve_unknowns=True removes this:
        # class `~dict`:
        #   def __setitem__(self, i: complex, y: float) -> NoneType
        #   def __setitem__(self, i: str, y: int) -> NoneType
        #   def values(self) -> list<float or int>
        # class `~list`:
        #   def __getitem__(self, index: int) -> float or int
      """)

  def testDictDefaults(self):
    with self.Infer("""
    def t_testDictDefaults(x):
      d = {}
      res = d.setdefault(x, str(x))
      _i_(d)
      return res
    def _i_(x):
      return x
    t_testDictDefaults(3)
    """, deep=False, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        def t_testDictDefaults(x: int) -> str
        # _i_ captures the more precise definition of the dict
        def _i_(x: dict<int, str>) -> dict<int, str>
        # TODO(pludemann): solve_unknowns=True removes this:
        # class `~dict`:
        #  def setdefault(self, k: int) -> str
        # class `~str`:
        #   def __init__(self, object: int) -> NoneType
      """)

  def testListInit0(self):
    with self.Infer("""
    def t_testListInit0(x):
      return list(x)
    """, deep=True, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        def t_testListInit0(x: object) -> list<?>
      """)

  def testListInit1(self):
    with self.Infer("""
    def t_testListInit1(x, y):
      return x + [y]
    """, deep=True, solve_unknowns=True, extract_locals=False) as ty:
      self.assertTypesMatchPytd(ty, """
        def t_testListInit1(x: list<object>, y) -> list<?>
      """)

  def testListInit2(self):
    with self.Infer("""
    def t_testListInit2(x, i):
      return x[i]
    z = __any_object__
    t_testListInit2(__any_object__, z)
    print z + 1
    """, deep=False, solve_unknowns=True, extract_locals=False) as ty:
      self.assertTypesMatchPytd(ty, """
        z: bool or complex or float or int or long

        def t_testListInit2(x: object, i: bool or complex or float or int or long) -> ?
      """)

  def testListInit3(self):
    with self.Infer("""
    def t_testListInit3(x, i):
      return x[i]
    t_testListInit3([1,2,3,'abc'], 0)
    """, deep=False, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        def t_testListInit3(x: list<int or str>, i: int) -> int or str
      """)

  def testListInit4(self):
    # TODO(kramm): This test takes over six seconds
    with self.Infer("""
    def t_testListInit4(x):
      return _i_(list(x))[0]
    def _i_(x):
      return x
    t_testListInit4(__any_object__)
    """, deep=False, solve_unknowns=True, extract_locals=True) as ty:
      # TODO(kramm): "object" below is only correct as long as return types and
      #              type params are covariant. If they'd be invariant, the
      #              below would be wrong.
      self.assertTypesMatchPytd(ty, """
        def t_testListInit4(x) -> ?
        # _i_ captures the more precise definition of the list
        def _i_(x: list<object>) -> list<?>
      """)

  def testAbsInt(self):
    with self.Infer("""
      def t_testAbsInt(x):
        return abs(x)
      t_testAbsInt(1)
    """, deep=False, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        def t_testAbsInt(x: int) -> int
    """)

  def testAbs(self):
    with self.Infer("""
      def t_testAbs(x):
        return abs(x)
      t_testAbs(__any_object__)
    """, deep=False, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        def t_testAbs(x: bool or complex or float or int or long) -> bool or float or int or long
      """)

  def testCmp(self):
    with self.Infer("""
      def t_testCmp(x, y):
        return cmp(x, y)
    """, deep=True, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
      def t_testCmp(x, y) -> bool
      """)

  def testCmpMulti(self):
    with self.Infer("""
      def t_testCmpMulti(x, y):
        return cmp(x, y)
      t_testCmpMulti(1, 2)
      t_testCmpMulti(1, 2.0)
      t_testCmpMulti(1.0, 2)
      # TODO(pludemann): add more tests
    """, deep=False, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        def t_testCmpMulti(x: float or int, y: int) -> bool
        def t_testCmpMulti(x: int, y: float) -> bool
      """)

  def testCmpStr(self):
    with self.Infer("""
      def t_testCmpStr(x, y):
        return cmp(x, y)
      t_testCmpStr("abc", "def")
    """, deep=False, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        def t_testCmpStr(x: str, y: str) -> bool
      """)

  def testCmpStr2(self):
    with self.Infer("""
      def t_testCmpStr2(x, y):
        return cmp(x, y)
      t_testCmpStr2("abc", __any_object__)
    """, deep=False, solve_unknowns=True, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        def t_testCmpStr2(x: str, y) -> bool
      """)

  def testTuple(self):
    # smoke test
    self.Infer("""
      def f(x):
        return x
      def g(args):
        f(*tuple(args))
    """, deep=True, solve_unknowns=False, extract_locals=False)

  def testOpen(self):
    with self.Infer("""
      def f(x):
        with open(x, "r") as fi:
          return fi.read()
      """, deep=True, solve_unknowns=True, extract_locals=False) as ty:
      self.assertTypesMatchPytd(ty, """
        def f(x: str or buffer or unicode) -> str
      """)

  def testSignal(self):
    with self.Infer("""
      import signal
      def f():
        signal.signal(signal.SIGALRM, 0)
    """, deep=True, solve_unknowns=True, extract_locals=False) as ty:
      self.assertTypesMatchPytd(ty, """
        signal: module

        def f() -> NoneType
      """)

  def testSysArgv(self):
    with self.Infer("""
      import sys
      def args():
        return ' '.join(sys.argv)
      args()
    """, deep=False, solve_unknowns=False, extract_locals=False) as ty:
      self.assertTypesMatchPytd(ty, """
        sys: module
        def args() -> str
      """)

  def testSetattr(self):
    with self.Infer("""
      class Foo(object):
        def __init__(self, x):
          for attr in x.__dict__:
            setattr(self, attr, getattr(x, attr))
    """, deep=True, solve_unknowns=False, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        class Foo(object):
          def __init__(self, x: ?) -> NoneType
      """)

  def testMap(self):
    with self.Infer("""
      def f(input_string, sub):
        return ''.join(map(lambda ch: ch, input_string))
    """, deep=True, solve_unknowns=True) as ty:
      self.assertOnlyHasReturnType(ty.Lookup("f"), self.str)

  def testArraySmoke(self):
    with self.Infer("""
      import array
      class Foo(object):
        def __init__(self):
          array.array('i')
    """, deep=True, solve_unknowns=False) as ty:
      ty.Lookup("Foo")  # smoke test

  def testArray(self):
    with self.Infer("""
      import array
      class Foo(object):
        def __init__(self):
          self.bar = array.array('i')
    """, deep=True, solve_unknowns=False) as ty:
      self.assertTypesMatchPytd(ty, """
        array: module
        class Foo(object):
          bar: array.array
          def __init__(self) -> NoneType
      """)

  def testInheritFromBuiltin(self):
    with self.Infer("""
      class Foo(list):
        pass
    """, deep=True, solve_unknowns=False) as ty:
      self.assertTypesMatchPytd(ty, """
        class Foo(list<?>):
          pass
      """)

  def testOsPath(self):
    with self.Infer("""
      import os
      class Foo(object):
        bar = os.path.join('hello', 'world')
    """, deep=True, solve_unknowns=True) as ty:
      ty.Lookup("Foo")  # smoke test

  def testIsInstance(self):
    with self.Infer("""
      class Bar(object):
        def foo(self):
          return isinstance(self, Baz)

      class Baz(Bar):
        pass
    """, deep=True, solve_unknowns=True) as ty:
      self.assertTypesMatchPytd(ty, """
      class Bar:
        def foo(self) -> bool

      class Baz(Bar):
        pass
      """)

  def testTime(self):
    with self.Infer("""
      import time
      def f(x):
        if x:
          return time.mktime(())
        else:
          return 3j
    """, deep=True, solve_unknowns=False, extract_locals=True) as ty:
      self.assertTypesMatchPytd(ty, """
        time: module

        def f(x: ?) -> complex
      """)


if __name__ == "__main__":
  test_inference.main()
