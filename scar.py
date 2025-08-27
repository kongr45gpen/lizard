from lizard import *

from pprint import pp, pformat
from typing import Any

from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import PythonLexer

from itertools import tee

from lizard_languages.code_reader import CodeStateMachine
from lizard_languages.rust import RustStates


def pprint_color(obj: Any) -> None:
    """Pretty-print in color."""
    print(highlight(pformat(obj, compact=True), PythonLexer(), Terminal256Formatter()), end="")

source_code_ada_tasks = """
task T is
   entry E(Z : access Integer);
end T;
13.c
task body T is
begin
   declare
      type A is access all Integer;
      X : A;
      Int : aliased Integer;

      function B(y: in integer) return float is
         n: float;
      begin
         put_line("Enter a real: ");
         get(n);
         return n * float(y);
      end B;

      task Inner;
      task body Inner is
        begin
            T.E(Int'Access);
        end Inner;
   begin
      accept E(Z : access Integer) do
         X := A(Z); -- Accessibility_Check
      end E;
   end;
end T;

Swap:
declare
      Temp : Integer;
   begin
      Temp := V; V := U; U := Temp;
   end Swap;
"""

source_code_ada_nested = """
with Ada.Text_IO; use Ada.Text_IO;
with Ada.Integer_Text_IO; use Ada.Integer_Text_IO;
with Ada.Strings.unbounded; use Ada.Strings.unbounded;
with Ada.Strings.unbounded.text_io; use Ada.Strings.unbounded.text_io;
with ada.Float_Text_IO; use Ada.Float_Text_IO;

function "+" (Left, Right : Integer_Array)
                return Integer_Array
    with Post =>
    (for all I in "+"'Result'Range =>
        "+"'Result (I) = Left (I) + Right (I));

overriding function Execute
     (Self    : access Diff_Head;
      Context : Interactive_Command_Context) return Command_Return_Type;

PROCEDURE scope is
   n: integer;

   procedure A(x: in integer) is
      z: float;

      function B(y: in integer) return float is
         n: float;
      begin
         put_line("Enter a real: ");
         get(n);
         return n * float(y);
      end B;

   begin
      z := B(x);
      put_line("Answer = ");
      put(z,2,4,0);
   end A;

begin
   put_line("Enter an integer: ");
   get(n);
   A(n);
end scope;
"""

source_code_ada = """
overriding function Execute
     (Self    : access Diff_Head;
      Context : Interactive_Command_Context) return Command_Return_Type;

with Ada.Text_IO;

-- This is a comment
procedure foo(bar: Integer) is
    Toast : Integer := 5
begin -- we begin because we have to
    if Line_Too_Short then
        raise Layout_Error;
    elsif Line_Full then
        New_Line;
        Put(Item);
    else
        Put(Item);
    end if;

    while Bid(N).Price < Cut_Off.Price loop
        Record_Bid(Bid(N).Price);
        N := N + 1;
    end loop;
    
    return bar;
end foo;

procedure Print_and_Increment (j: in out Number) is

    function Next (k: in Number) return Number is
    begin
      return k + 1;
    end Next;

  begin
    Ada.Text_IO.Put_Line ( "The total is: " & Number'Image(j) );
    j := Next (j);
  end Print_and_Increment;

OK
"""

source_code_py = """
class SoNice(CodeStateMachine):  # pylint: disable=R0903
    def __init__(self, context, niceness):
        super(SoNice, self).__init__(context)
        self.niceness = niceness

    def _increase_nice(self, verygood):
        if verygood == 'nice':
            print("Ok I am happy")

    def _emotion(self, feeling):
        if feeling != ':(':
            self.context.restart_new_emotion(feeling)
            self.context.add_to_long_emotion_name(":(")
        else:
            self._state = self._sadden

    def _sadden(self, feeling):
        if feeling == ':)':
            self._state = self._state_joy
        elif feeling == ':[':
            self._state = self._state_emotion_detail
        else:
            self.context.emote(feeling)
            return
        self.context.add_to_long_emotion_name(" " + feeling)

    def _state_joy(self, feeling):
        if feeling == ':':
            self.next(self._state_first_smile)
        else:
            self.next(self._state_global)

    def _state_first_smile(self, feeling):
        self._state = self._state_global
            self.context.add_nloc(-feeling.count('\n') - 1)
        self._state_global(feeling)

    def _state_emotion_detail(self, feeling):
        self.context.add_to_long_emotion_name(" " + feeling)
        if feeling == ':]':
            self._state = self._sadden

def wow_omg():
    print("wow omg")
"""

source_code_rs = """
pub fn clock(instant: Instant) -> EffectNodeDefinition {
    EffectNodeDefinition {
        name: "Clock".to_string(),
        help: Some("The system clock in float seconds".to_string()),
        parameters: vec![],
        node_type: NodeType::Input,
        processor: Box::new(move |_, _, _| {
            let time = instant.elapsed().as_secs_f64();

            if time > 0.0 {
                print("time is zero") // the time is zero
                if time > 1.0 {
                    print("time is three")
                }
            }

            pub fn lock() {
                print("wow");
            }

            debug!("Clock: {}", time);

            Ok(NodeDataset::new_single(smallvec![ViewValue::F64(time)]))
        }),
    }
}
"""

# results: FileInformation = analyze_file.analyze_source_code("a.adb", source_code)

filename = "a.adb"
source_code = source_code_ada_nested

context = FileInfoBuilder(filename)
reader = (get_reader_for(filename) or CLikeReader)(context)
tokens = reader.generate_tokens(source_code)

print("Tokens:")
tokens, tokens2 = itertools.tee(tokens)
pprint_color(list(tokens2))

def state(pstates):
    list = []

    for s in pstates:
        if hasattr(s._state, '__name__'):
            list.append(s._state.__name__)
        # if type of s is RustStates
        elif isinstance(s, CodeStateMachine):
            list.append(state([s._state]))
        else:
            raise ValueError("Unknown state type")

    return list

try:
    for processor in analyze_file.processors:
        tokens = processor(tokens, reader)
        tokens, tokens2 = itertools.tee(tokens)
        print(f"For processor: {processor}")
        pprint_color(list(tokens2))

    print("\n")

    for rd in reader(tokens, reader):
        tokens, tokens2 = itertools.tee(tokens)


        # if context._nesting_stack.pending_function is not None:
        for function in context.stacked_functions + [context.current_function]:
            print('|' + function.name, end='')
            # print(function., end=' ')
            # print(function, end=' ')
        print(highlight('@' + str(context._nesting_stack.current_nesting_level), PythonLexer(), Terminal256Formatter()).strip(), end="")
        print(f" : {rd}", end=' ')
    
        pprint_color(state(reader.parallel_states))

        pass
except RecursionError as e:
    sys.stderr.write(
        "[skip] fail to process '%s' with RecursionError - %s\n" %
        (filename, e))

# print("Function list:")
# pprint_color(results.function_list)

# print("Filename")
# pprint_color(results.filename)

# pprint_color(results.)

print("Results:")
pprint_color(vars(context.fileinfo))