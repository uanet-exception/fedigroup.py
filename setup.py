import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="fedigroup.py",
    version="1.0.2",
    author="Dmytro Poltavchenko",
    author_email="dmytro.poltavchenko@gmail.com",
    description="Emulate group accounts on Mastodon/Pleroma",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/uanet-exception/fedigroup.py",
    packages=setuptools.find_packages(),
    keywords="mastodon pleroma toot group fediverse",
    python_requires='>=3',
    classifiers=[
        "Environment :: Console",
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "Mastodon.py",
    ],
    scripts=["fedigroup.py"],
)
