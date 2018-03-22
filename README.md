# Introduction

This script allows to generate native bindings for these languages directly from radare2 C headers:

 - Python (uses [ctypeslib2](https://github.com/trolldbois/ctypeslib))
 - Rust (uses [rust-bindgen](https://github.com/rust-lang-nursery/rust-bindgen))
 - Go (uses [c-for-go](https://github.com/xlab/c-for-go))
 - Haskell (uses [c2hs](https://github.com/haskell/c2hs))

More languages are planned, in particular:

 - Ruby - I wanted to use [ffi-gen](https://github.com/neelance/ffi_gen) but it needs revival and update to the modern Ruby and Clang.
 - OCaml - needs to be written
 - Lua - maybe [LuaAutoC](https://github.com/orangeduck/LuaAutoC) can be used, I don't know.

# Usage

`genbind.py -o /tmp/r2bindings-output`

The tool required `radare2` to be installed and takes the include directory from the output of `r2 -H`
