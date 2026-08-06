# SPDX-FileCopyrightText: 2026 The HeiChips Contributors
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
{
  buildPythonPackage,
  fetchPypi,
  more-itertools,
  networkx,
  pydantic,
  typing-extensions,
}:

buildPythonPackage rec {
  pname = "nortl";
  version = "1.6.0";
  format = "wheel";

  src = fetchPypi {
    inherit pname version format;
    dist = "py3";
    python = "py3";
    hash = "sha256-ovulDfHC9fS5OdeBFboTbRsKVXzZysGtc1jUfMb/xKU=";
  };

  dependencies = [
    more-itertools
    networkx
    pydantic
    typing-extensions
  ];

  pythonImportsCheck = [ "nortl" ];

  meta.description = "Not-only RTL";
}
