import unittest
from lizard import analyze_file, FileAnalyzer, get_extensions
from lizard_languages.ada import AdaReader
import pickle
import re


def get_ada_function_list(source_code):
    return analyze_file.analyze_source_code(
        "a.adb", source_code).function_list

class Test_tokenizing_Ada(unittest.TestCase):

    def check_tokens(self, expect, source):
        tokens = list(AdaReader.generate_tokens(source))
        self.assertEqual(expect, tokens)

    def test_tokenizing_ada_comments(self):
        self.check_tokens(['-- comment more'], '-- comment more')
        self.check_tokens(['-- comment more', '\n', 'another'], '-- comment more\nanother')

#     def test_tokenizing_ruby_regular_expression(self):
#         self.check_tokens(['/ab/'], '/ab/')
#         self.check_tokens([r'/\//'], r'/\//')
#         self.check_tokens([r'/a/igm'], r'/a/igm')

#     def test_should_not_confuse_division_as_regx(self):
#         self.check_tokens(['a','/','b',',','a','/','b'], 'a/b,a/b')
#         self.check_tokens(['3453',' ','/','b',',','a','/','b'], '3453 /b,a/b')

#     def test_tokenizing_ruby_regular_expression(self):
#         self.check_tokens(['a', '=', '/ab/'], 'a=/ab/')

#     def test_tokenizing_ruby_comments(self):
#         self.check_tokens(['/**a/*/'], '''/**a/*/''')

#     def test_tokenizing_pattern(self):
#         self.check_tokens(['/\//'], r'''/\//''')

#     def test_tokenizing_brackets(self):
#         self.check_tokens(['{', '}'], r'''{}''')

#     def test_tokenizing_string_with_formatter(self):
#         self.check_tokens(['""', '${', '1', '}', '"a"' ], r'''"#{1}a"''')

#     def test_tokenizing_string_with_string(self):
#         self.check_tokens(['""', '${', '"a"', '}', '""' ], r'''"#{"a"}"''')

#     def test_tokenizing_string_with_string2(self):
#         self.check_tokens(['""', '${', '"/"', '${', '}', '""', '}', '""'], r'''"#{"/#{}"}"''')

#     def test_tokenizing_symbol(self):
#         self.check_tokens([':class'], r''':class''')
#         self.check_tokens([':class?'], r''':class?''')
#         self.check_tokens([':@class'], r''':@class''')

#     def test_shorthand_symbol(self):
#         self.check_tokens(['class:', 'a'], r'''class:a''')

#     def test_tokenizing_string_expression(self):
#         self.check_tokens(['%{"}'], r'''%{"}''')
#         self.check_tokens(['%{""}'], r'''%{""}''')
#         self.check_tokens(['%{\}}'], r'''%{\}}''')
#         self.check_tokens(['%{\}}'], r'''%{\}}''')
#         self.check_tokens(['%q{\}}'], r'''%q{\}}''')
#         self.check_tokens(['%q[\]]'], r'''%q[\]]''')
#         self.check_tokens(['%q<\>>'], r'''%q<\>>''')

#     def test_vars(self):
#         self.check_tokens(['$a'], r'''$a''')
#         self.check_tokens(['@a'], r'''@a''')
#         self.check_tokens(['@@a'], r'''@@a''')

#     def test_ranges(self):
#         self.check_tokens(['..'], r'''..''')
#         self.check_tokens(['...'], r'''...''')

#     def test_special_method_names(self):
#         self.check_tokens(['a!'], r'''a!''')
#         self.check_tokens(['a?'], r'''a?''')

#     def test_MyToken_serialization(self):
#         # Test with regex match object
#         match = re.match(r'\w+', 'test123')
#         token = MyToken(match)
#         pickled = pickle.dumps(token)
#         unpickled = pickle.loads(pickled)
#         self.assertEqual(str(token), str(unpickled))
#         self.assertEqual(token.begin, unpickled.begin)
        
#         # Test with plain string
#         token_str = MyToken('test123')
#         pickled_str = pickle.dumps(token_str)
#         unpickled_str = pickle.loads(pickled_str)
#         self.assertEqual(str(token_str), str(unpickled_str))
#         self.assertEqual(token_str.begin, unpickled_str.begin)


class Test_parser_for_Ada(unittest.TestCase):

    def test_empty(self):
        functions = get_ada_function_list("")
        self.assertEqual(0, len(functions))

    def test_no_function(self):
        result = get_ada_function_list('''with Ada.Text_IO;''')
        self.assertEqual(0, len(result))

    def test_one_procedure(self):
        result = get_ada_function_list('''
            procedure F is
            begin
                null;
            end F;
                ''')
        self.assertEqual(1, len(result))
        self.assertEqual("F", result[0].name)
        self.assertEqual(0, result[0].parameter_count)
        self.assertEqual(1, result[0].cyclomatic_complexity)
        self.assertEqual(4, result[0].length)

    def test_one_function(self):
        result = get_ada_function_list('''
            function F return Integer is
            begin
                return 42;
            end F;
                ''')
        self.assertEqual(1, len(result))
        self.assertEqual("F", result[0].name)
        self.assertEqual(0, result[0].parameter_count)
        self.assertEqual(1, result[0].cyclomatic_complexity)
        self.assertEqual(4, result[0].length)

    def test_one_function_loc(self):
        result = get_ada_function_list('''
            procedure F is begin
                something;
                something;
            end F;
                ''')
        self.assertEqual(4, result[0].length)
        self.assertEqual(4, result[0].nloc)

    def test_two_functions(self):
        result = get_ada_function_list('''
            procedure F is begin
            end F;
            procedure G is begin
            end G;
                ''')
        self.assertEqual(2, len(result))
        self.assertEqual("G", result[1].name)

    def test_null_procedures(self):
        result = get_ada_function_list('''
            procedure F (Msg : String) is null;
            procedure G is null;
                ''')
        self.assertEqual(2, len(result))
        self.assertEqual("F", result[0].name)
        self.assertEqual(1, result[0].nloc)
        self.assertEqual("G", result[1].name)
        self.assertEqual(1, result[1].nloc)

    def test_subprogram_declaration(self):
        result = get_ada_function_list('''
            procedure Proc
                (Var1 : Integer;
                Var2 : out Integer;
                Var3 : in out Integer);

            function Func (Var : Integer) return Integer;
                ''')
        self.assertEqual(2, len(result))
        self.assertEqual("Proc", result[0].name)
        self.assertEqual("Func", result[1].name)

    def test_subprogram_rename(self):
        result = get_ada_function_list('''
                procedure Print renames Message.Print;
            ''')
        self.assertEqual(1, len(result))
        self.assertEqual("Print", result[0].name)

    def test_function_generic_instantiation(self):
        result = get_ada_function_list('''
            function Convert1 is new Ada.Unchecked_Conversion (System.Address, Msg_Pointer.Pointer);
                ''')
        self.assertEqual(1, len(result))
        self.assertEqual("Convert1", result[0].name)

    def test_function_contracts(self):
        result = get_ada_function_list('''
            function Divide (Left, Right : Float) return Float
                with Pre  => Right /= 0.0,
                Post => Divide'Result * Right < Left + 0.0001
                    and then Divide'Result * Right > Left - 0.0001;
        ''')
        self.assertEqual(1, len(result))
        self.assertEqual("Divide", result[0].name)


    def test_complex_subprogram(self):
        result = get_ada_function_list('''
            package body Pack is

            procedure Last_Chance_Handler(Msg : in System.Address; Line : in Integer) is
                type Msg_Indices is range 1 .. 16;
                type Msg_Arr is array (Msg_Indices range <>) of aliased Word;
                type Day_Of_Month is new Integer range 1 .. 31;

                function Convert1 is new Ada.Unchecked_Conversion (System.Address, Msg_Pointer.Pointer);
                function Convert2 (Var : Integer) return Integer is begin
                    null;
                end
            begin
                --  TODO: Read PC from SP
                for J in 1 .. 16 loop
                    Qemu.DEBUG.MESSAGE (J) := Word (Msg_Str.all);
                    Increment (Msg_Str);
                end loop;

            end Last_Chance_Handler;

            end Pack;
        ''')
        self.assertEqual(3, len(result))
        self.assertEqual("Pack::Last_Chance_Handler", result[0].name)
        self.assertEqual("Pack::Convert1", result[1].name)
        self.assertEqual("Pack::Convert2", result[2].name)


#     def test_one_with_begin_and_end(self):
#         result = get_ruby_function_list('''
#             def f
#                 begin
#                     something
#                 end
#             end
#                 ''')
#         self.assertEqual(5, result[0].nloc)

#     def test_one_with_begin_and_end_outside(self):
#         result = get_ruby_function_list('''
#         begin
#             def f
#                 begin
#                 end
#             end
#         end
#                 ''')
#         self.assertEqual(4, result[0].nloc)

#     def test_one_with_brackets_and_end_outside(self):
#         result = get_ruby_function_list('''
#         {
#             def f
#                 begin
#                 end
#             end
#         }
#                 ''')
#         self.assertEqual(4, result[0].nloc)

#     def test_string(self):
#         result = get_ruby_function_list('''
#   def path_with_locale(params, to)
#     xx
#     "#{"a"}"
#     xx
#   end

#   mount JasmineRails::Engine => '/specs' if defined?(JasmineRails)
# end
#                 ''')
#         self.assertEqual(5, result[0].nloc)

#     def test_one_with_class_in_it(self):
#         result = get_ruby_function_list('''
#             def f
#                 class a
#                 end
#                 module a
#                 end
#             end
#                 ''')
#         self.assertEqual(6, result[0].nloc)

#     def test_one_with_class_as_identifier(self):
#         result = get_ruby_function_list('''
#             def f
#                 a.class
#             end
#                 ''')
#         self.assertEqual(3, result[0].nloc)

#     def test_one_with_do(self):
#         result = get_ruby_function_list('''
#             def f
#                 x do
#                     something
#                 end
#             end
#                 ''')
#         self.assertEqual(5, result[0].nloc)

#     def test_one_within_do(self):
#         result = get_ruby_function_list('''
#             x do
#                 def f
#                     something
#                 end
#             end
#                 ''')
#         self.assertEqual(3, result[0].nloc)

#     def test_one_within_embedded_doc(self):
#         result = get_ruby_function_list('''
# =begin
#     def f
#     end
# =end
#                 ''')
#         self.assertEqual(0, len(result))

#     def test_one_within_embedded_doc_harder(self):
#         result = get_ruby_function_list('''
# =begin
# the everything between a line beginning with =begin and
# that with =end will be skipped by the interpreter.
#     def f
#     end
# =end
# def f
# end
#                 ''')
#         self.assertEqual(1, len(result))


# class Test_parser_for_Ruby_ccn(unittest.TestCase):

#     def test_basic_complexity(self):
#         result = get_ruby_function_list('''
#             def f
#                 if a
#                 elsif b
#                 end
#             end
#                 ''')
#         self.assertEqual(3, result[0].cyclomatic_complexity)


# class Test_parser_for_Ruby_if_while_for(unittest.TestCase):
#     def test_basic_if_block(self):
#         result = get_ruby_function_list('''
#             def f
#                 if a
#                 end
#             end
#                 ''')
#         self.assertEqual(4, result[0].nloc)

#     def test_basic_if_oneliner_block(self):
#         result = get_ruby_function_list('''
#             def f; if a; end; end
#                 ''')
#         self.assertEqual(1, result[0].nloc)

#     def test_basic_if_modifier(self):
#         result = get_ruby_function_list('''
#             def f
#                 a if b
#             end
#                 ''')
#         self.assertEqual(3, result[0].nloc)

#     def test_basic_if_with_then_on_one_line(self):
#         result = get_ruby_function_list('''
#             def f
#                 a = if b then c else d end
#             end
#                 ''')
#         self.assertEqual(3, result[0].nloc)

#     def test_unless(self):
#         result = get_ruby_function_list('''
#             def f
#                 a = unless b then c else d end
#             end
#                 ''')
#         self.assertEqual(3, result[0].nloc)

#     def test_basic_while_block(self):
#         result = get_ruby_function_list('''
#             def f
#                 while a
#                 end
#                 for a
#                 end
#             end
#                 ''')
#         self.assertEqual(6, result[0].nloc)

#     def test_basic_while_modifier(self):
#         result = get_ruby_function_list('''
#             def f
#                 a while a
#             end
#                 ''')
#         self.assertEqual(3, result[0].nloc)

#     def test_while_with_do(self):
#         result = get_ruby_function_list('''
#             def f
#                 while a do
#                 end
#             end
#                 ''')
#         self.assertEqual(4, result[0].nloc)

#     def test_while_modifier_with_block(self):
#         result = get_ruby_function_list('''
#             def f
#                 begin
#                 end while a
#             end
#                 ''')
#         self.assertEqual(4, result[0].nloc)

#     def test_class_as_an_symbol(self):
#         result = get_ruby_function_list('''
#             def f
#                 begin
#                 end while a
#             end
#                 ''')
#         self.assertEqual(4, result[0].nloc)


#     def test_rspec_it(self):
#         result = get_ruby_function_list('''
#             describe 'xx' do
#               it "does something" do
#               end
#               it "does something else" do
#               end
#               context "xx" do
#                 it "xxxx" do
#                     xxx
#                 end
#               end
#             end
#                 ''')
#         self.assertEqual(3, result[2].nloc)

#     def test_rspec_it_with_brackets(self):
#         result = get_ruby_function_list('''
#             describe 'xx' do
#               it { }
#               it "does something else" do
#                 a if b
#               end
#               context "xx" do
#                 it "xxxx" do
#                     xxx
#                 end
#               end
#             end
#                 ''')
#         self.assertEqual(3, len(result))
#         self.assertEqual(1, result[0].nloc)
#         self.assertEqual(1, result[0].cyclomatic_complexity)

#     def test_it_as_variable(self):
#         result = get_ruby_function_list('''
#             describe 'xx' do
#               it = 3
#             end
#                 ''')
#         self.assertEqual(0, len(result))







# class Test_parser_for_Ruby_def(unittest.TestCase):
#     def test_class_method(self):
#         result = get_ruby_function_list('''
#             def a.b
#             end
#                 ''')
#         self.assertEqual("a.b", result[0].name)
#         self.assertEqual(0, result[0].parameter_count)

#     def test_empty_parameters(self):
#         result = get_ruby_function_list('''
#             def a()
#             end
#                 ''')
#         self.assertEqual(0, result[0].parameter_count)

#     def test_more_parameters(self):
#         result = get_ruby_function_list('''
#             def a(b,c)
#             end
#                 ''')
#         self.assertEqual(2, result[0].parameter_count)
