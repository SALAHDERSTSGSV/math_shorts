from __future__ import annotations

import re

import sympy as sp
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    standard_transformations,
    parse_expr,
)

from domain.artifacts import GeneratedContent, MathVerificationResult


class MathVerificationError(Exception):
    """Base exception for mathematical verification failures."""


class MathVerifier:
    """
    Deterministic mathematical verification layer.

    Responsibilities:
    - Extract the equation from the generated problem.
    - Parse mathematical expressions safely enough for the current DSL.
    - Verify that solution transformations preserve the equation.
    - Solve the original problem symbolically.

    Gemini is NOT trusted to decide whether the mathematics is correct.
    """

    _EQUATION_PATTERN = re.compile(
        r"^\s*(?P<left>.+?)\s*=\s*(?P<right>.+?)\s*$"
    )

    _SOLVE_PREFIX = re.compile(
        r"^\s*(?:solve|find|calculate|determine)\s+",
        re.IGNORECASE,
    )

    _TRANSFORMATIONS = (
        standard_transformations
        + (implicit_multiplication_application,)
    )

    def verify(
        self,
        content: GeneratedContent,
    ) -> MathVerificationResult:

        checks: list[str] = []

        try:
            problem_expression = self._extract_problem_expression(
                content.problem
            )

            checks.append("problem_expression_parsed")

            expressions = self._extract_solution_expressions(
                content.solution_steps
            )

            checks.append("solution_expressions_parsed")

            parsed_expressions = [
                self._parse_mathematical_expression(expression)
                for expression in expressions
            ]

            checks.append("solution_expressions_valid")

            self._verify_equation_chain(
                expressions,
                parsed_expressions,
            )

            checks.append("equation_transformations_valid")

            verified_solution = self._solve_problem(
                problem_expression
            )

            checks.append("problem_solved_symbolically")

            return MathVerificationResult(
                valid=True,
                problem=content.problem,
                verified_solution=verified_solution,
                checks=tuple(checks),
            )

        except Exception as exc:
            return MathVerificationResult(
                valid=False,
                problem=content.problem,
                verified_solution="",
                checks=tuple(checks),
                error=str(exc),
            )

    # ------------------------------------------------------------------
    # Problem extraction
    # ------------------------------------------------------------------

    def _extract_problem_expression(
        self,
        problem: str,
    ) -> str:
        """
        Convert:

            Solve 3*x = x^9

        into:

            3*x = x^9
        """

        cleaned = self._SOLVE_PREFIX.sub("", problem.strip())

        match = self._EQUATION_PATTERN.match(cleaned)

        if not match:
            raise MathVerificationError(
                "Problem does not contain a recognizable equation."
            )

        return (
            f"{match.group('left').strip()} = "
            f"{match.group('right').strip()}"
        )

    # ------------------------------------------------------------------
    # Solution extraction
    # ------------------------------------------------------------------

    def _extract_solution_expressions(
        self,
        steps: tuple[str, ...],
    ) -> list[str]:
        """
        Extract equations from solution steps.

        Examples:

            "Move all terms to one side: x^9 - 3*x = 0"

        becomes:

            "x^9 - 3*x = 0"
        """

        expressions: list[str] = []

        for step in steps:
            cleaned = step.strip()

            match = self._EQUATION_PATTERN.search(cleaned)

            if not match:
                continue

            left = match.group("left").strip()
            right = match.group("right").strip()

            expressions.append(
                f"{left} = {right}"
            )

        if not expressions:
            raise MathVerificationError(
                "No mathematical equations were found "
                "in the solution steps."
            )

        return expressions

    # ------------------------------------------------------------------
    # Expression parsing
    # ------------------------------------------------------------------

    def _parse_mathematical_expression(
        self,
        expression: str,
    ) -> tuple[sp.Expr, sp.Expr]:

        match = self._EQUATION_PATTERN.match(
            expression.strip()
        )

        if not match:
            raise MathVerificationError(
                f"Invalid mathematical expression: {expression}"
            )

        left = self._parse_side(
            match.group("left")
        )

        right = self._parse_side(
            match.group("right")
        )

        return left, right

    def _parse_side(
        self,
        expression: str,
    ) -> sp.Expr:

        expression = expression.strip()

        if not expression:
            raise MathVerificationError(
                "Empty mathematical expression."
            )

        # Convert mathematical exponent notation:
        #
        # x^9
        #
        # into SymPy/Python notation:
        #
        # x**9
        expression = expression.replace("^", "**")

        # Discover simple variable names.
        variable_names = set(
            re.findall(
                r"\b[a-zA-Z]\b",
                expression,
            )
        )

        symbols = {
            name: sp.Symbol(name)
            for name in variable_names
        }

        try:
            return parse_expr(
                expression,
                local_dict=symbols,
                transformations=self._TRANSFORMATIONS,
                evaluate=True,
            )

        except Exception as exc:
            raise MathVerificationError(
                f"Cannot parse expression: {expression}"
            ) from exc

    # ------------------------------------------------------------------
    # Equation transformation verification
    # ------------------------------------------------------------------

    def _verify_equation_chain(
        self,
        expressions: list[str],
        parsed_expressions: list[
            tuple[sp.Expr, sp.Expr]
        ],
    ) -> None:
        """
        Verify consecutive equation transformations.

        We compare:

            left - right

        rather than comparing the raw equations.

        Example:

            3*x = x^9

        gives:

            3*x - x^9

        while:

            x^9 - 3*x = 0

        gives:

            x^9 - 3*x

        These differ only by -1, so they represent
        the same equation.
        """

        for index in range(
            len(parsed_expressions) - 1
        ):
            current_left, current_right = (
                parsed_expressions[index]
            )

            next_left, next_right = (
                parsed_expressions[index + 1]
            )

            current_difference = sp.expand(
                current_left - current_right
            )

            next_difference = sp.expand(
                next_left - next_right
            )

            if self._equations_are_equivalent(
                current_difference,
                next_difference,
            ):
                continue

            raise MathVerificationError(
                "Invalid solution transformation between "
                f"'{expressions[index]}' and "
                f"'{expressions[index + 1]}'."
            )

    def _equations_are_equivalent(
        self,
        first: sp.Expr,
        second: sp.Expr,
    ) -> bool:
        """
        Determine whether two equations have the same
        algebraic meaning.

        First we check whether one expression is a
        non-zero constant multiple of the other.

        Examples:

            x - 3
            x - 3

            => ratio = 1

            3*x - x^9
            x^9 - 3*x

            => ratio = -1

        Both are equivalent.
        """

        first = sp.factor(first)
        second = sp.factor(second)

        if sp.simplify(first - second) == 0:
            return True

        if first == 0 or second == 0:
            return False

        try:
            ratio = sp.cancel(
                first / second
            )

            if (
                ratio.is_number
                and ratio != 0
            ):
                return True

        except Exception:
            pass

        # If we cannot prove equivalence algebraically,
        # reject instead of guessing.
        return False

    # ------------------------------------------------------------------
    # Solving
    # ------------------------------------------------------------------

    def _solve_problem(
        self,
        equation: str,
    ) -> str:

        left, right = (
            self._parse_mathematical_expression(
                equation
            )
        )

        symbols = sorted(
            left.free_symbols | right.free_symbols,
            key=lambda symbol: symbol.name,
        )

        if not symbols:
            raise MathVerificationError(
                "Problem contains no symbolic variable."
            )

        if len(symbols) != 1:
            raise MathVerificationError(
                "Current verifier supports one symbolic variable."
            )

        variable = symbols[0]

        solution = sp.solve(
            sp.Eq(left, right),
            variable,
        )

        return sp.sstr(solution)
