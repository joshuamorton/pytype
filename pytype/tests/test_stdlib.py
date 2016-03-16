"""Tests of selected stdlib functions."""


from pytype.tests import test_inference


class StdlibTests(test_inference.InferenceTest):
  """Tests for files in typeshed/stdlib."""

  def testAST(self):
    with self.Infer("""
      import ast
      def f():
        return ast.parse("True")
    """, deep=True, solve_unknowns=True) as ty:
      self.assertTypesMatchPytd(ty, """
        ast = ...  # type: module
        def f() -> _ast.AST
      """)

  def testUrllib(self):
    with self.Infer("""
      import urllib
    """, deep=True, solve_unknowns=True) as ty:
      self.assertTypesMatchPytd(ty, """
        urllib = ...  # type: module
      """)


if __name__ == "__main__":
  test_inference.main()
