from setuptools import setup


def readme():
    with open('README.md', 'r', encoding='utf-8') as f:
        return f.read()


setup(
    name='argser',
    version='0.0.1',
    description='argparse without boilerplate',
    long_description=readme(),
    long_description_content_type='text/markdown',
    author='Bachynin Ivan',
    author_email='bachynin.i@gmail.com',
    url='https://github.com/vaniakosmos/args_parse',
    license='MIT',
    python_requires='>=3.6',
    extras_require={
        'tabulate': ['tabulate'],
        'dev': ['pytest'],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Utilities',
    ],
    keywords=['flags', 'argparse'],
)
