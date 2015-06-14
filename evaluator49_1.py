#from evaluatorLibrary import *
from consLibrary import *
from evaluator48 import *

def map_for_scheme(proc_obj, args):
    """
    proc_obj: ('procedure (param1 param2) (op1 param1 param2))
    proc_obj: ('primitive car) ('primitive cons)
    """
    if isPrimitiveProcedure(proc_obj):
        return mapp(primitive_implementation(proc_obj), args)
    else:
        if isNull(args):
            return EmptyList
        return cons(eval_sequence(procedure_body(proc_obj),
                        extend_environment(procedure_params(proc_obj),
                                            List(car(args)),
                                            procedure_environment(proc_obj))),
                    map_for_scheme(proc_obj, cdr(args)))

DEFINE = Symbol("define")
IF = Symbol("if")
BEGIN = Symbol("begin")
PROCEDURE = Symbol("procedure")
SET_BANG = Symbol("set!")
LAMBDA = Symbol("lambda")
COND = Symbol("cond")
ELSE = Symbol("else")
LET = Symbol("let")

WHILE = Symbol("while")
LOOP = Symbol("loop")
FOR = Symbol("for")
BODY = Symbol("body")

#def let2combination(exp):
#    """
#    (let foo ((x 1) (y 2)) <body>)
#    (let ((x 1) (y 2)) <body>)
#    output: ( (LAMBDA (var1 ... varn) <body>) e1 e2 ... en )
#    """
#    names = let_names(exp)
#    body = let_body(exp)
#    lambda_e = make_lambda(names, body)
#    if isNamedLet(exp):
#        label = let_label(exp)
#        define_variable(label, m_eval(lambda_e, env), env)  # bind label to PROCEDURE in env
#    return cons(lambda_e, let_exps(exp))

# ('while e1 'loop e2 e3 e4)
def make_while(e1, e2, *args):
    """
    args: tuple of expressions
    """
    args = [e2] + list(args)
    exp_list = List(*args)
    return cons(WHILE, cons(e1, cons(LOOP, exp_list)))

def isWhile(exp):
    return isTaggedList(exp, WHILE)

def while_pred(exp):
    """
    input: (WHILE e1 LOOP e2 e3 e4)
    output: e1
    """
    return cadr(exp)

def while_body(exp):
    """
    input: (WHILE e1 LOOP e2 e3 e4)
    output: (e2 e3 e4)
    """
    return cdddr(exp)

def while_to_named_let(exp):
    """
    input: while exp
    output: named let
    (WHILE e1 LOOP e2 e3 e4) -> (let name () (if e1 (begin e2 e3 e4 name) #f) )
    """
    foo = Symbol("foo")

    e1 = while_pred(exp)
    bindings = make_bindings()
    exps = while_body(exp)
    exps = append(exps, List(List(foo)))
    body = seq2exp(exps) # (BEGIN e2 e3 e4 (foo))
    let_body = make_if(e1, body, FALSE)
    e = make_named_let(foo, bindings, let_body) # make named_let
    return e

# ('for init_t test_exp incr_proc 'body e1 e2 e3)
def make_for(init_t, test_e, incr_e, *exps):
    """
    output: (FOR init_t test_e incr_exp BODY e1 e2 e3)
    init_t: (x exp)  # init tuple
    test_e: (< x 5)
    incr_e: (+ x 1)
    """
    args = [init_t, test_e, incr_e]
    body = List(BODY, *exps)
    return append(List(FOR, *args), body)

def isFor(exp):
    return isTaggedList(exp, FOR)

def for_init(exp):
    """
    output: (x e0)
    """
    return cadr(exp)

def for_test(exp):
    """
    output: (< x 5)
    """
    return caddr(exp)

def for_incr(exp):
    """
    output: (+ x 1)
    """
    return cadddr(exp)

def for_body(exp):
    """
    output: (e1 e2 e3)
    """
    return cddr(cdddr(exp))

def for_to_named_let(exp):
    """
    input: (FOR init_t test_e incr_e BODY e1 e2 e3)
    output: (let foo ((x e0)) (if test_e (begin e1 e2 e3 (set! x incr_e) (foo)) FALSE))
    """
    foo = Symbol("foo")
    init_t = for_init(exp)
    test_e = for_test(exp)
    incr_e = for_incr(exp)
    body = for_body(exp)

    var = car(init_t)
    e0 = cadr(init_t)
    bindings = make_bindings([var, e0])

    body_beg = seq2exp(append(body, List(List(SET_BANG, x, incr_e), List(foo, x))))
    let_body = make_if(test_e, body_beg, FALSE)
    return make_named_let(foo, bindings, let_body)




### The Core Evaluator
def m_eval(exp, env):
    if isSelfEvaluating(exp):
        return exp
    elif isVariable(exp):
        return lookup_variable_value(exp, env)
    elif isQuoted(exp):
        return text_of_quotation(exp)
    elif isAssignment(exp):
        return eval_assignment(exp, env)
    elif isDefinition(exp):
        return eval_definition(exp, env)
    elif isIf(exp):
        return eval_if(exp, env)
    elif isLambda(exp):
        print("in isLambda", "env: ")
        pprint(caar(env))
        return make_procedure(lambda_params(exp), lambda_body(exp), env)
    elif isBegin(exp):
        return eval_sequence(begin_actions(exp), env)
    elif isCond(exp):
        return m_eval(cond2if(exp), env)
    elif isLet(exp):
        pprint(exp)
        #return m_eval(let2combination(exp), env)      # this doesn't work; even if let2combination is in this module
        return m_eval(let2combination2(exp, env), env) # this works because env is a parameter to let2combination2 (I am confused)
    elif isWhile(exp):
        pprint(exp)
        return m_eval(while_to_named_let(exp), env)
    elif isFor(exp):
        pprint(exp)
        return m_eval(for_to_named_let(exp), env)
    elif isApplication(exp):
        return m_apply(m_eval(operator(exp), env), list_of_values(operands(exp), env))
    else:
        raise TypeError("Unknown expression type -- EVAL")

def eval_assignment(exp, env):
    """
    re-bind the value of an exisiting variable in env
    """
    set_variable_value(assignment_variable(exp), m_eval(assignment_value(exp), env), env)
    return quote("ok")

def eval_definition(exp, env):
    """
    create and bind a variable in the current frame
    re-bind a variable in the current frame
    """
    define_variable(definition_variable(exp), m_eval(definition_value(exp), env), env)
    return quote("ok")

def eval_if(exp, env):
    if m_eval(if_predicate(exp), env) == FALSE:
        # pred is FALSE
        return m_eval(if_alternative(exp), env)
    else:
        return m_eval(if_consequent(exp), env)
def eval_sequence(exps, env):
    """
    (e1 e2 e3) => (v1 v2 v3)
    returns the value of the last exp
    """
    if isLastExp(exps):
        return m_eval(first_exp(exps), env)
    else:
        m_eval(first_exp(exps), env)
        return eval_sequence(rest_exps(exps), env)
def list_of_values(exps, env):
    if isNoOperands(exps):
        return EmptyList
    else:
        return cons(m_eval(first_operand(exps), env),
                    list_of_values(rest_operands(exps), env))
def cond2if(cond_exp):
    """
    ("'cond"  (c1 e1)
              (c2 e2)
              (c3 e3)
              ('"else" e4)
    )
    produces a nested if_exp
    (if c1 e1
          (if c2 e2
                 (if c3 e3)))
    """
    def expand_clauses(list_of_clauses):        
        if isNull(list_of_clauses):
            return FALSE  # 4-15
        first = first_clause(list_of_clauses)
        rest = rest_clauses(list_of_clauses)
        if isElseClause(first):
            if isNull(rest):
                return seq2exp(cond_actions(first)) 
            else:
                raise ValueError("ELSE clause is not last -- cond2if")
        else:
            return make_if(
                    cond_predicate(first),
                    seq2exp(cond_actions(first)), # make a single "'begin" expression
                    expand_clauses(rest))
    return expand_clauses(cond_clauses(cond_exp)) # 4-15 changed exp to cond_exp

def m_apply(proc, args):
    if isPrimitiveProcedure(proc):
        return apply_primitive_procedure(proc, args)
    elif isCompoundProcedure(proc):
        return eval_sequence(procedure_body(proc), extend_environment(procedure_params(proc), args, 
                                                                      procedure_environment(proc)))
    else:
        raise TypeError("Unknown procedure type -- APPLY")


### Representing Expressions

def isTaggedList(exp, tag):
    """returns True if exp is tagged with tag"""
    return isPair(exp) and isinstance(car(exp), Symbol) and (car(exp).name == tag.name)

def isSelfEvaluating(exp):
    return isNumber(exp) or isString(exp) or isBool(exp)

def isQuoted(exp):
    return isTaggedList(exp, QUOTE)

def text_of_quotation(exp):
    """
    returns datum as a List
    (QUOTE datum)
    """
    return cadr(exp)

# (SET_BANG var value)
def isVariable(exp):
    return isSymbol(exp)
def isAssignment(exp):
    return isTaggedList(exp, SET_BANG)
def assignment_variable(exp):
    return cadr(exp)
def assignment_value(exp):
    return caddr(exp)

# (DEFINE var value)
# (DEFINE (foo x y) body)
def isDefinition(exp):
    return isTaggedList(exp, DEFINE)
def definition_variable(exp):
    if isSymbol(cadr(exp)):
        return cadr(exp)
    else:
        return caadr(exp)
def definition_value(exp):
    if isSymbol(cadr(exp)):
        return caddr(exp)
    else:
        params = cdadr(exp)
        body = cddr(exp)
        make_lambda(params, body)

# (LAMBDA (p1 p2) exp1 exp2)
def isLambda(exp):
    return isTaggedList(exp, LAMBDA)
def lambda_params(lambda_exp):
    """
    (x y z)
    """
    return cadr(lambda_exp)
def lambda_body(lambda_exp):
    """
    input: (LAMBDA (x y) e1 e2 e3 )
    returns ( e1 e2 e3 )
    """
    return cddr(lambda_exp)
def make_lambda(params, body):
    """
    params: (p1 p2 p3 ...)
    body: ( exp1 exp2 )
    (LAMBDA (p1 p2 p3) exp1 exp2)
    """
    return cons(LAMBDA, cons(params, body))

# ('if e1 e2 e3)
def isIf(exp):
    return isTaggedList(exp, IF)
def if_predicate(exp):
    return cadr(exp)
def if_consequent(exp):
    return caddr(exp)
def if_alternative(exp):
    if not isNull(cdddr(exp)):
        return cadddr(exp)
    else:
        #return False
        return FALSE  # 5/3 False -> FALSE
def make_if(pred, conseq, alt):
    return List(IF, pred, conseq, alt)

# ('cond  (c1 n1) (c2 n2) (else n3) )
def isCond(exp):
    return isTaggedList(exp, COND)
def cond_clauses(cond_exp):
    return cdr(cond_exp) # 4-15 changed exp to cond_exp
def first_clause(list_of_clauses):
    return car(list_of_clauses)
def rest_clauses(list_of_clauses):
    return cdr(list_of_clauses)
def cond_predicate(clause):
    """
    returns c of (c e)
    """
    return car(clause)
def cond_actions(clause):
    """
    (c e1 e2 e3) is a list
    clause can have 1 or more actions
    """
    return cdr(clause)
def isElseClause(clause):
    return cond_predicate(clause) == ELSE


# (begin e1 e2 e3)
def isBegin(exp):
    return isTaggedList(exp, BEGIN)
def begin_actions(beg_exp):
    return cdr(beg_exp)
def isLastExp(seq):
    """
    seq: (e1)
    """
    return isNull(cdr(seq))
def first_exp(seq):
    """
    seq: (e1 e2 ... )
    output: e1
    """
    return car(seq)
def rest_exps(seq):
    """
    seq: (e1 e2 e3)
    output: (e2 e3)
    """
    return cdr(seq)
def seq2exp(seq):
    """
    produces a single exp from a seq of expressions
    """
    if isNull(seq):
        """empty sequence"""
        return seq
    elif isLastExp(seq):
        """
        seq: (e)
        output: e
        """
        return first_exp(seq)
    else:
        """convert seq to a 'begin exp"""
        return make_begin(seq)
def make_begin(seq):
    return cons(BEGIN, seq)

# application of proc to args
# (operator arg1 arg2 arg3)
def isApplication(exp):
    """used after all special forms are tested"""
    return isPair(exp)
def operator(app):
    """
    returns a variable that is the name of the procedure_object
    """
    return car(app)
def operands(app):
    """
    returns a list of values
    These are the values to which the operator is applied.
    """
    return cdr(app)
def isNoOperands(args):
    return isNull(args)
def first_operand(args):
    return car(args)
def rest_operands(args):
    return cdr(args)

### Representing Procedures
# (PROCEDURE (p1 p2 p3) (exp1 exp2) env)
def make_procedure(params, body, env):
    """evaluates a procedure definition
    returns a closure
    (closure is tagged as 'procedure)"""
    return List(PROCEDURE, params, body, env)
def isCompoundProcedure(exp):
    return isTaggedList(exp, PROCEDURE)
def procedure_params(proc):
    return cadr(proc)
def procedure_body(proc):
    return caddr(proc)
def procedure_environment(proc):
    return cadddr(proc)

### Representing Environments
# frame: ( list_of_variables list_of_values )
# Implement environments as a list of frames; parent environment is
# the cdr of the list. Each frame will be implemented as a list
# of variables and a list of corresponding values.
def enclosing_env(env):
    return cdr(env)
def first_frame(env):
    return car(env)
the_empty_environment = EmptyList

def make_frame(variables, values):
    """
    variables: (var1 var2 var3)
    values: (val1 val2 val3)
    output: (variables values)
    """
    return cons(variables, values)
def frame_variables(frame):
    """
    frame: ( (var1 var2 var3) (val1 val2 val3) )
    """
    return car(frame)
def frame_values(frame):
    return cdr(frame)
def addBindingToFrame(var, val, frame):
    """
    frame -> ( (new_var var1 var2 var3) (new_val val1 val2 val3) )
    """
    set_car(frame, cons(var, frame_variables(frame)))
    set_cdr(frame, cons(val, frame_values(frame)))
    return
def extend_environment(vars, vals, base_env):
    """
    vars: (var1 var2 var3)
    vals: (val1 val2 val3)
    base_env: env
    """
    if isNull(vars):
        return base_env
    if length(vars) == length(vals):
        return cons(make_frame(vars, vals), base_env)
    elif length(vars) > length(vals):
        raise ValueError("extend_environment -- too few args")
    else:
        raise ValueError("extend_environment -- too many args")

# lookup in the environment chain
def lookup_variable_value(var, env):
    """
    returns a value or UnboundLocalError
    """
    def env_loop(environment):
        """
        calls scan on each frame in the env list
        """
        def scan(vars, vals):
            """
            scans variables in a frame
            """
            if isNull(vars):
                return env_loop(enclosing_env(environment))  # 5-4: env -> environment
            elif isEq(var, car(vars)) == TRUE:
                return car(vals)
            else:
                return scan(cdr(vars), cdr(vals))
        if environment is the_empty_environment:
            raise UnboundLocalError("lookup_variable")
        frame = first_frame(environment)
        return scan(frame_variables(frame), frame_values(frame))
    return env_loop(env)

def set_variable_value(var, val, env):
    """
    sets a var to a val, if var is found, else UnboundLocalError
    """
    def env_loop(environment):
        """
        calls scan on each frame in the env list
        """
        def scan(vars, vals):
            """
            scans variables in a frame
            """
            if isNull(vars):
                return env_loop(enclosing_env(environment)) # 5-4: env -> environment
            elif var == car(vars):
                return set_car(vals, val) #4-15
            else:
                return scan(cdr(vars), cdr(vals)) # 4-15
        if environment is the_empty_environment:
            raise UnboundLocalError("lookup_variable")
        frame = first_frame(environment)
        return scan(frame_variables(frame), frame_values(frame)) # 4-15
    return env_loop(env) # 4-15

def define_variable(var, val, env):
    """
    re-binds an existing variable or creates a new binding
    in the current frame
    """
    frame = first_frame(env)
    def scan(vars, vals):
        if isNull(vars):
            return addBindingToFrame(var, val, frame)
        elif var == car(vars):
            return set_car(vals, val)
        else:
            return scan(cdr(vars), cdr(vals))
    return scan(frame_variables(frame), frame_values(frame))

### Primitive Procedures and the Initial Environment
# ('primitive primitive_name primitive_op)
# for ex: ('primitive 'car car)

primitive_procedures = List(List(CAR, car),
                            List(CDR, cdr),
                            List(CDDR, cddr),
                            List(CDDDR, cdddr),
                            List(CADDDR, cadddr),
                            List(CADR, cadr),
                            List(CADDR, caddr),
                            List(CAADR, caadr),
                            List(CDADR, cdadr),
                            List(CADR, cadr),
                            List(CONS, cons),
                            List(ISNULL, isNull),
                            List(ISPAIR, isPair),
                            List(ISSYMBOL, isSymbol),
                            List(ISNUMBER, isNumber),
                            List(ISSTRING, isString),
                            List(ISQUOTED, isQuoted),
                            List(SET_CAR, set_car),
                            List(SET_CDR, set_cdr),
                            List(PLUS, plus),
                            List(MINUS, minus),
                            List(MULT, mult),
                            List(DIV, divide),
                            List(GT, greaterthan),
                            List(LT, lessthan),
                            List(LE, lessthanequalto), # added this 5/22 in this module
                            List(EQUALTO, equalto),
                            List(ISEQ, isEq),
                            List(ISEQUAL, isEqual),
                            List(OR, or_lispy),
                            List(AND, and_lispy),
                            List(ASSOC, assoc),
                            List(MAPP, mapp),
                            List(MAPP_S, map_for_scheme),
                            List(DISPLAY, pprint),
                            List(LIST, List))


def primitive_procedure_names():
    """
    returns list of names of primitive procedures
    """
    return mapp(car, primitive_procedures)
def primitive_procedure_objects():
    """
    returns a list of: ( (PRIMITIVE primitive_implementation) ... )
    for ex:
    ( (PRIMITIVE car) (PRIMITIVE cdr) (PRIMITIVE cons) (PRIMITIVE plus) ... )
    """
    return mapp(lambda proc: List(PRIMITIVE, primitive_implementation(proc)), primitive_procedures)

def isPrimitiveProcedure(proc_object):
    return isTaggedList(proc_object, PRIMITIVE)
def primitive_implementation(primitive_proc):
    return cadr(primitive_proc)
def apply_primitive_procedure(proc_object, args):
    """
    invokes the primitive procedure on the arg list (args)
    args is a scheme List of values
    """
    args_py = convertToPythonList(args)
    return primitive_implementation(proc_object)(*args_py)

def setup_environment():
    initial_env = extend_environment(primitive_procedure_names(),  # ("'cons", "'+", ...)
                                    primitive_procedure_objects(), # ((PRIMITIVE, cons) (PRIMITIVE, plus)...)
                                    the_empty_environment)
    define_variable(TRUE, True, initial_env)
    define_variable(FALSE, False, initial_env)
    return initial_env

#the_global_environment = setup_environment()

          

###################
if __name__ == "__main__":
    env = setup_environment()

    # Test for FOR iteration
    x = Symbol("x")
    e = make_for(List(x, 2), List(LE, x, 25), List(MULT, x, x), List(DISPLAY, x))
    m_eval(e, env)
    print()


    # Test for WHILE iteration
    BLASTOFF = Symbol("blastoff")

    def blastoff(n):
        """
        output: (BLASTOFF n)

        patterned after this:

        while count > 0:
            print(count)
            count -= 1
        print(blastoff!)
        """
        count = Symbol("count")
        
        while_exp = make_while(List(GT, count, 0), List(DISPLAY, count), List(SET_BANG, count, List(MINUS, count, 1)))
        lambda_e = make_lambda(List(count), List(while_exp, "blastoff!"))  # (LAMBDA (count) while_exp "blastoff!")
        define_variable(BLASTOFF, m_eval(lambda_e, env), env)  # BLASTOFF bounded to PROCEDURE in env
        return List(BLASTOFF, n)

    e = blastoff(5)
    pprint(e)
    pprint(m_eval(e, env))
    print()
    
    




    
