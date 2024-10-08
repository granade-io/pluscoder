# import pytest
# from unittest.mock import patch, mock_open
# from pluscoder.repomap import generate_tree
# from pluscoder.io_utils import io


# @pytest.fixture
# def mock_python_file_content():
#     return b"""
# def my_function():
#     \"\"\"This is an example function\"\"\"
#     pass

# class ExampleClass:
#     \"\"\"This is an example class.\"\"\"

#     def example_method(self):
#         # This is an example method.
#         pass
#     def example_method2(self):
#         \"\"\"This is an example method 2.\"\"\"
#         pass
# """


# @pytest.fixture
# def mock_javascript_file_content():
#     return b"""
# function exampleFunction() {
#   // This is an example function
#   console.log('Hello, world!');
# }

# class ExampleClass {
#   constructor() {
#     this.property = 'value';
#   }

#   method() {
#     // This is an example method
#     return this.property;
#   }
# }
# """


# @pytest.fixture
# def mock_jsx_file_content():
#     return b"""
# import React from 'react';

# function ExampleComponent({ prop }) {
#     /* Some comment */
#   return (
#     <div>
#       <h1>Example Component</h1>
#       <p>{prop}</p>
#     </div>
#   );
# }

# export default ExampleComponent;
# """


# @pytest.fixture
# def mock_ts_file_content():
#     return b"""
# // A simple function in TypeScript
# function addNumbers(a: number, b: number): number {
#     return a + b;
# }

# // A class with a method in TypeScript
# class Calculator {
#     private initialValue: number;

#     constructor(initialValue: number) {
#         this.initialValue = initialValue;
#     }

#     public addToValue(addend: number): number {
#         /* add to value function */
#         return this.initialValue + addend;
#     }
# }
# """


# @pytest.fixture
# def mock_tsx_file_content():
#     return b"""
# // A simple function in TSX
# function addNumbers(a: number, b: number): number {
#     return a + b;
# }

# // A class component with a method in TSX
# class Calculator extends React.Component<{ initialValue: number }, {}> {
#     addToValue(addend: number): number {
#         /* add to value function */
#         return this.props.initialValue + addend;
#     }

#     render() {
#         const sum = this.addToValue(5);
#         return (
#             <div>
#                 <p>Sum: {sum}</p>
#             </div>
#         );
#     }
# }
# """


# @patch("pluscoder.repomap.os.walk")
# @patch("pluscoder.repomap.open", new_callable=mock_open)
# @patch("pluscoder.repomap.should_include_file")
# def test_generate_tree(
#     mock_should_include, mock_file_open, mock_walk, mock_python_file_content
# ):
#     # Mock os.walk to return one Python file
#     mock_walk.return_value = [("/repo_root", [], ["example.py"])]

#     # Mock should_include_file to return True for our file
#     mock_should_include.return_value = True

#     # Mock file open to return our example content
#     mock_file_open.return_value.read.return_value = mock_python_file_content

#     # Call generate_tree
#     result = generate_tree(
#         repo_path="/repo_root",
#         include_patterns=["*.py"],
#         exclude_patterns=[],
#         level=2,
#         tracked_files=["example.py"],
#         io=io,
#     )

#     # Define expected output
#     expected_output = """
# example.py
# ==========
# def my_function():
#     This is an example function
# class ExampleClass:
#     This is an example class.
#     def example_method(self):
#     def example_method2(self):
#         This is an example method 2.
# ==========
# """

#     # Assert the result matches the expected output
#     assert result.strip() == expected_output.strip()

#     # Verify that the mocks were called correctly
#     mock_walk.assert_called_once_with("/repo_root")
#     mock_should_include.assert_called_once_with(
#         "/repo_root/example.py", ["example.py"], ["*.py"], [], "/repo_root"
#     )
#     mock_file_open.assert_called_once_with("/repo_root/example.py", "rb")


# @patch("pluscoder.repomap.os.walk")
# @patch("pluscoder.repomap.open", new_callable=mock_open)
# @patch("pluscoder.repomap.should_include_file")
# def test_generate_tree_javascript(
#     mock_should_include, mock_file_open, mock_walk, mock_javascript_file_content
# ):
#     # Mock os.walk to return one JavaScript file
#     mock_walk.return_value = [("/repo_root", [], ["example.js"])]

#     # Mock should_include_file to return True for our file
#     mock_should_include.return_value = True

#     # Mock file open to return our example content
#     mock_file_open.return_value.read.return_value = mock_javascript_file_content

#     # Call generate_tree
#     result = generate_tree(
#         repo_path="/repo_root",
#         include_patterns=["*.js"],
#         exclude_patterns=[],
#         level=2,
#         tracked_files=["example.js"],
#         io=io,
#     )

#     # Define expected output
#     expected_output = """
# example.js
# ==========
# function exampleFunction() {
#     // This is an example function
# class ExampleClass {
#     constructor() {
#     method() {
#         // This is an example method
# ==========
# """

#     # Assert the result matches the expected output
#     assert result.strip() == expected_output.strip()

#     # Verify that the mocks were called correctly
#     mock_walk.assert_called_once_with("/repo_root")
#     mock_should_include.assert_called_once_with(
#         "/repo_root/example.js", ["example.js"], ["*.js"], [], "/repo_root"
#     )
#     mock_file_open.assert_called_once_with("/repo_root/example.js", "rb")


# @patch("pluscoder.repomap.os.walk")
# @patch("pluscoder.repomap.open", new_callable=mock_open)
# @patch("pluscoder.repomap.should_include_file")
# def test_generate_tree_jsx(
#     mock_should_include, mock_file_open, mock_walk, mock_jsx_file_content
# ):
#     # Mock os.walk to return one JSX file
#     mock_walk.return_value = [("/repo_root", [], ["example.jsx"])]

#     # Mock should_include_file to return True for our file
#     mock_should_include.return_value = True

#     # Mock file open to return our example content
#     mock_file_open.return_value.read.return_value = mock_jsx_file_content

#     # Call generate_tree
#     result = generate_tree(
#         repo_path="/repo_root",
#         include_patterns=["*.jsx"],
#         exclude_patterns=[],
#         level=2,
#         tracked_files=["example.jsx"],
#         io=io,
#     )

#     # Define expected output
#     expected_output = """
# example.jsx
# ===========
# function ExampleComponent({ prop }) {
#     /* Some comment */
# ===========
# """

#     # Assert the result matches the expected output
#     assert result.strip() == expected_output.strip()

#     # Verify that the mocks were called correctly
#     mock_walk.assert_called_once_with("/repo_root")
#     mock_should_include.assert_called_once_with(
#         "/repo_root/example.jsx", ["example.jsx"], ["*.jsx"], [], "/repo_root"
#     )
#     mock_file_open.assert_called_once_with("/repo_root/example.jsx", "rb")


# @patch("pluscoder.repomap.os.walk")
# @patch("pluscoder.repomap.open", new_callable=mock_open)
# @patch("pluscoder.repomap.should_include_file")
# def test_generate_tree_ts(
#     mock_should_include, mock_file_open, mock_walk, mock_ts_file_content
# ):
#     # Mock os.walk to return one TypeScript file
#     mock_walk.return_value = [("/repo_root", [], ["example.ts"])]

#     # Mock should_include_file to return True for our file
#     mock_should_include.return_value = True

#     # Mock file open to return our example content
#     mock_file_open.return_value.read.return_value = mock_ts_file_content

#     # Call generate_tree
#     result = generate_tree(
#         repo_path="/repo_root",
#         include_patterns=["*.ts"],
#         exclude_patterns=[],
#         level=2,
#         tracked_files=["example.ts"],
#         io=io,
#     )

#     # Define expected output
#     expected_output = """
# example.ts
# ==========
# function addNumbers(a: number, b: number): number {
# class Calculator {
#     constructor(initialValue: number) {
#     public addToValue(addend: number): number {
#         /* add to value function */
# ==========
# """

#     # Assert the result matches the expected output
#     assert result.strip() == expected_output.strip()

#     # Verify that the mocks were called correctly
#     mock_walk.assert_called_once_with("/repo_root")
#     mock_should_include.assert_called_once_with(
#         "/repo_root/example.ts", ["example.ts"], ["*.ts"], [], "/repo_root"
#     )
#     mock_file_open.assert_called_once_with("/repo_root/example.ts", "rb")


# @patch("pluscoder.repomap.os.walk")
# @patch("pluscoder.repomap.open", new_callable=mock_open)
# @patch("pluscoder.repomap.should_include_file")
# def test_generate_tree_tsx(
#     mock_should_include, mock_file_open, mock_walk, mock_tsx_file_content
# ):
#     # Mock os.walk to return one TSX file
#     mock_walk.return_value = [("/repo_root", [], ["example.tsx"])]

#     # Mock should_include_file to return True for our file
#     mock_should_include.return_value = True

#     # Mock file open to return our example content
#     mock_file_open.return_value.read.return_value = mock_tsx_file_content

#     # Call generate_tree
#     result = generate_tree(
#         repo_path="/repo_root",
#         include_patterns=["*.tsx"],
#         exclude_patterns=[],
#         level=2,
#         tracked_files=["example.tsx"],
#         io=io,
#     )

#     # Define expected output
#     expected_output = """
# example.tsx
# ===========
# function addNumbers(a: number, b: number): number {
# class Calculator extends React.Component<{ initialValue: number }, {}> {
#     addToValue(addend: number): number {
#         /* add to value function */
#     render() {
# ===========
# """

#     # Assert the result matches the expected output
#     assert result.strip() == expected_output.strip()

#     # Verify that the mocks were called correctly
#     mock_walk.assert_called_once_with("/repo_root")
#     mock_should_include.assert_called_once_with(
#         "/repo_root/example.tsx", ["example.tsx"], ["*.tsx"], [], "/repo_root"
#     )
#     mock_file_open.assert_called_once_with("/repo_root/example.tsx", "rb")
