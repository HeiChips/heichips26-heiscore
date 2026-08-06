# SPDX-FileCopyrightText: 2026 The HeiChips Contributors
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
{
  lib,
  stdenv,
  cmake,
  boost,
  prjpeppercorn-src,
}:

stdenv.mkDerivation {
  pname = "prjpeppercorn-tools";
  version = "0-unstable-2026-02-25";

  src = prjpeppercorn-src;
  sourceRoot = "${prjpeppercorn-src.name}/libgm";

  nativeBuildInputs = [ cmake ];
  buildInputs = [ boost ];

  cmakeFlags = [ (lib.cmakeBool "STATIC_BUILD" false) ];

  meta.description = "GateMate bitstream packer/unpacker from Project Peppercorn";
}
