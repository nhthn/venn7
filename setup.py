import setuptools

extras_require = {
    "test": ["black == 19.10b0", "pytest"],
}

setuptools.setup(
    name="venn7",
    version="0.0.1",
    license="UNLICENSED",
    description="Some tools for rendering pretty 7-fold Venn diagrams.",
    author="Nathan Ho",
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=["numpy >= 1.19.4, < 1.20", "sympy", "shapely"],
    extras_require=extras_require,
)
