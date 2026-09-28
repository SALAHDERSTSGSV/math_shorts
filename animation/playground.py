from manim import *


class MathVideo(Scene):
    def construct(self):

        # ============================================================
        # 1. TITLE
        # ============================================================

        title = Text(
            "Manim",
            font_size=108,
            font="DejaVu Serif",
        )

        title.to_edge(UP, buff=0.65)
        title.shift(LEFT * 1.2)

        self.play(
            Write(title),
            run_time=1.2,
        )

        # ============================================================
        # 2. GEOMETRIC OBJECTS
        # ============================================================

        square = Square(
            side_length=1.8,
            fill_opacity=0.65,
            stroke_width=2,
        )

        square.set_fill(
            color=BLUE_E,
            opacity=0.65,
        )

        square.move_to(
            RIGHT * 4.2 + UP * 0.8
        )

        circle = Circle(
            radius=1.25,
            fill_opacity=0.65,
            stroke_width=2,
        )

        circle.set_fill(
            color=GREEN,
            opacity=0.65,
        )

        circle.move_to(
            RIGHT * 3.2 + DOWN * 0.2
        )

        triangle = Triangle(
            fill_opacity=0.65,
            stroke_width=2,
        )

        triangle.set_fill(
            color=RED_E,
            opacity=0.65,
        )

        triangle.scale(1.45)

        triangle.move_to(
            RIGHT * 4.4 + DOWN * 1.0
        )

        # ============================================================
        # 3. ANIMATE THE SHAPES
        # ============================================================

        self.play(
            GrowFromCenter(square),
            GrowFromCenter(circle),
            GrowFromCenter(triangle),
            lag_ratio=0.15,
            run_time=1.4,
        )

        # ============================================================
        # 4. SUBTITLE
        # ============================================================

        subtitle = Text(
            "All systems operational!",
            font_size=43,
            font="DejaVu Serif",
        )

        subtitle.to_edge(
            DOWN,
            buff=0.65,
        )

        subtitle.shift(
            LEFT * 2.25
        )

        self.play(
            FadeIn(
                subtitle,
                shift=UP * 0.25,
            ),
            run_time=0.8,
        )

        # ============================================================
        # 5. MATHEMATICAL EXPRESSION
        # ============================================================

        equation = MathTex(
            r"\oint_{\gamma} f(z)\,dz = 0",
            font_size=48,
        )

        equation.move_to(
            RIGHT * 4.1 + DOWN * 2.25
        )

        self.play(
            Write(equation),
            run_time=1.0,
        )

        # ============================================================
        # 6. INTERACTION / TRANSFORMATION
        # ============================================================

        equation_highlight = SurroundingRectangle(
            equation,
            buff=0.12,
            corner_radius=0.08,
        )

        self.play(
            Create(equation_highlight),
            run_time=0.5,
        )

        self.play(
            Indicate(
                equation,
                scale_factor=1.12,
            ),
            run_time=0.8,
        )

        # ============================================================
        # 7. FINAL SCENE
        # ============================================================

        self.wait(0.8)

        self.play(
            FadeOut(
                title,
                subtitle,
                square,
                circle,
                triangle,
                equation,
                equation_highlight,
            ),
            run_time=0.8,
        )

        self.wait(0.2)
