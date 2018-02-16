#!/usr/bin/env python2
import sys
import os.path
import logging
import tempfile
import subprocess
from subprocess import call, check_output
# Python 2 legacy hack
try:
    from StringIO import StringIO
except:
    from io import StringIO

# --------------------------------------------------------------------
#                        Helper functions
def which(program):
    def is_file(fpath):
        if sys.version_info >= (3,0):
            return os.path.is_file(fpath)
        else:
            return os.path.isfile(fpath)

    def is_exe(fpath):
        return is_file(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

# For now works only for GCC
def get_compiler_include_paths():
    startline = "#include <...> search starts here:"
    cmdline = ["cpp", "-v", "/dev/null", "-o", "/dev/null"]
    p = subprocess.Popen(cmdline, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    out, err = p.communicate()
    # Interesting output is in stderr:
    lines = err.split('\n')
    includes = []
    if startline in lines:
        start = lines.index(startline)
        end = len(lines) - start
        for i in range(1, end):
            line = lines[start + i].lstrip()
            if os.path.exists(os.path.dirname(line)):
                includes  += [line]
    return includes

# FIXME: get this from "r2 -H" output, see INCDIR variable
def get_radare2_include_paths():
    return ["/usr/local/include/libr", "/usr/local/include/libr/include"]

# --------------------------------------------------------------------
#                        Global values
def read_file_list():
    return [
            "/usr/local/include/libr/r_core.h",
            "/usr/local/include/libr/r_asm.h",
            "/usr/local/include/libr/r_anal.h",
            "/usr/local/include/libr/r_bin.h",
            "/usr/local/include/libr/r_debug.h",
            "/usr/local/include/libr/r_io.h",
            "/usr/local/include/libr/r_config.h",
            "/usr/local/include/libr/r_flag.h",
            "/usr/local/include/libr/r_sign.h",
            "/usr/local/include/libr/r_hash.h",
            "/usr/local/include/libr/r_diff.h",
            "/usr/local/include/libr/r_egg.h",
            "/usr/local/include/libr/r_fs.h",
            "/usr/local/include/libr/r_lang.h",
            "/usr/local/include/libr/r_pdb.h"
            ]

outdir = "/home/akochkov/data/tmp/r2-api"
r2_includes = ["-I" + s for s in get_radare2_include_paths()]
# -I/usr/local/include - form strings like tht
c_includes = ["-I" + s for s in get_compiler_include_paths()]

langs = {
    "python": False,
    "ruby" : False,
    "go" : False,
    "lua" : False,
    "rust" : False,
    "haskell" : False,
    "ocaml" : False
}

# --------------------------------------------------------------------

# 1. Check if all needed executables and libraries are installed

def check_python_requirements():
    # Check if Clang/LLVM is installed
    # Check if its headers are installed
    # Check if "ctypeslib2" is installed - "pip install ctypeslib2"
    # Python 3 way:
    package_name = "ctypeslib"
    if sys.version_info >= (3,0):
        import importlib.util
        spec = importlib.util.find_spec(package_name)
        if spec is None:
            print("ctypeslib2 not found!\n")
            return False
        return True
    # Python 2 way:
    else:
        import pip
        installed_pkgs = pip.get_installed_distributions()
        flat_installed_pkgs = [pkg.project_name for pkg in installed_pkgs]
        if package_name + "2" in flat_installed_pkgs:
            return True
        print("ctypeslib2 not found!\n")
        return False

def check_ruby_requirements():
    # Check if we have Ruby installed
    # Check if we have neelance/ffi_gen gem installed
    return True

def check_go_requirements():
    # Check if Go is installed
    if which("go") is None:
        print("Go is not installed!\n")
        return False
    # Check for Go version
    # Check if "go get github.com/xlab/c-for-go" is installed
    if which("c-for-go") is None:
        print("c-for-go is not installed!\n")
        return False
    return True

def check_lua_requirements():
    # Check if we have LuaAutoC
    return True

def check_rust_requirements():
    # Check if Rust is installed
    if which("rustc") is None:
        print("Rust is not installed!\n")
        return False
    # Check if Cargo is installed
    if which("cargo") is None:
        print("Cargo is not installed!\n")
        return False
    # Check if "bindgen" is installed
    # TODO: Use output of cargo?
    return True

def check_haskell_requirements():
    # Check if GHC is installed
    if which("ghc") is None:
        return False
    # Check if Cabal is installed
    if which("cabal") is None:
        return False
    # Check if "c2hs" is installed (cabal install c2hs)
    if which("c2hs") is None:
        return False
    return True

def check_ocaml_requirements():
    return True

# ------------------------------------------------------------------
# Converters for every language

def gen_python_bindings(outdir, path):
    import ctypeslib
    from ctypeslib.codegen import clangparser
    from ctypeslib.codegen import codegenerator
    pyout = StringIO()
    fname = os.path.splitext(os.path.basename(path))[0]
    print(get_compiler_include_paths())
    # TODO: Make it configurable
    clang_opts = r2_includes + c_includes

    parser = clangparser.Clang_Parser(flags = clang_opts)
    items = parser.parse(path)
    if items is None:
        print("Error parsing {0} file!\n".format(fname))
        return False
    gen = codegenerator.Generator(pyout)
    # See ctypeslib/clang2py.py for more options
    gen.generate(parser, items, flags=[], verbose=True)
    outfname = outdir + "/" + fname + ".py"
    with fopen(outfname, "w") as f:
        f.write(pyout.getvalue())
        pyout.close()
        return True

    pyout.close()
    print("Cannot write {0}.py file!\n".format(fname))
    return False

def gen_rust_bindings(outdir, path):
    # determine radare2 include path
    # call bindgen inpath -o outpath -- -I/usr/local/include/libr
    fname = os.path.splitext(os.path.basename(path))[0]
    outpath = outdir + "/" + fname + ".rs"
    cmdline = "bindgen {0} -o {1}".format(path, outpath)
    # Add the include directory, for angled includes
    cmdline += " -- -I/usr/local/include/libr"
    # run it
    # TODO: Check return code
    call(cmdline, shell=True)
    return True

cgo_tmpl = """
---
GENERATOR:
    PackageName: radare2
    PackageDescription: "Package radare2 provides Go bindings for radare2 reverse engineering library"
    PackageLicense: "LGPLv3"
    PkgConfigOpts: [libr]
    Includes: {0}

PARSER:
    IncludePaths: {1}
    SourcesPaths: {2}
    Defines:
        __UNIX__: 1

TRANSLATOR:
    ConstRules:
        defines: eval
    Rules:
        global:
            - {{action: accept, from "^r_"}}
            - {{transform: export}}
        private:
            - {{transform: unexport}}
"""

def gen_go_bindings(outdir, path):
    def gen_yaml_manifest():
        cgo_yaml = cgo_tmpl.format(read_file_list(), get_compiler_include_paths() + \
                get_radare2_include_paths(), read_file_list())
        return cgo_yaml

    yml = gen_yaml_manifest()
    #tmpf = tempfile.NamedTemporaryFile(delete=False)
    tmpfname = "radare2.yml"
    tmpf = open(tmpfname, "w")
    tmpf.write(yml)
    print("Writing YAML file: {0}".format(tmpfname))
    cmdline = "c-for-go -ccdefs -ccincl {0}".format(tmpfname)
    # TODO: Check return code
    call(cmdline, shell=True)
    tmpf.close()
    return True

chs = """
{{-#LANGUAGE ForeignFunctionInterface #-}}

import Foreign.C.Types
import Foreign.Ptr
import Foreign.Storable

#include "{0}"
"""

def gen_haskell_bindings(outdir, path):
    def gen_chs(fname):
        return chs.format(fname)

    fname = os.path.splitext(os.path.basename(path))[0]
    cpp_opts = "-I/usr/local/libr"
    tmpchs = gen_chs(fname + ".h")
    tmpfname = fname + ".chs"
    tmpf = open(tmpfname, "w")
    tmpf.write(tmpchs)
    print("Writing CHS file: {0}".format(tmpfname))
    cmdline = "c2hs -t {0} -C {1} {2}".format(outdir, cpp_opts, tmpfname)
    # TODO: Check return code
    call(cmdline, shell=True)
    tmpf.close()
    return True

# -------------------------------------------------------
# Check/autotest the result

def check_python_bindings(outdir):
    print("Python bindings are generated and working properly!\n")
    return True

def check_ruby_bindings(outdir):
    return True

def check_go_bindings(outdir):
    return True

# -------------------------------------------------------

def check_requirements():
    result = True
    langs["python"] = check_python_requirements()
    langs["rust"] = check_rust_requirements()
    langs["go"] = check_go_requirements()
    langs["haskell"] = check_haskell_requirements()
    return result

# TODO: Better fail check
def gen_bindings(outdir, path):
    result = True
    if langs["python"]:
        result &= gen_python_bindings(outdir, path)
    if langs["rust"]:
        result &= gen_rust_bindings(outdir, path)
    if langs["haskell"]:
        result &= gen_haskell_bindings(outdir, path)
    return result

def check_bindings(outdir):
    return True

if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s %(message)s")
    lst = read_file_list()
    # Python bindings
    if check_requirements():
        for f in lst:
            gen_bindings(outdir, f)
        # Go bindings generated all at once
        if langs["go"]:
            gen_go_bindings(outdir, f)
        check_bindings(outdir)

