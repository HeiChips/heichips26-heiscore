# SPDX-FileCopyrightText: 2026 The HeiChips Contributors
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
#
# Project-local packages, layered on top of nix-eda/librelane's package set.
# Applied in flake.nix, so everything defined here is reachable as pkgs.<name>
# and is built against the nixpkgs that librelane itself is built against.

final: prev: {
  prjpeppercorn-src = final.fetchFromGitHub {
    owner = "YosysHQ";
    repo = "prjpeppercorn";
    rev = "bc3df10ff30ee342b944aff5d85283a26b7de342";
    hash = "sha256-pz7s1EzZ0iEOJRfOJU80um7QgY5JO3WpDMfQS4E6G5c=";
  };

  gmtools = final.callPackage ./gmtools.nix { };

  nextpnr = prev.nextpnr.overrideAttrs (old: {
    cmakeFlags =
      (builtins.filter (
        flag: !(final.lib.hasPrefix "-DHIMBAECHEL_UARCH" flag) && !(final.lib.hasPrefix "-DBUILD_TESTS" flag)
      ) old.cmakeFlags)
      ++ [
        (final.lib.cmakeFeature "HIMBAECHEL_UARCH" "example;gowin;ng-ultra;gatemate")
        (final.lib.cmakeFeature "HIMBAECHEL_PEPPERCORN_PATH" "${final.prjpeppercorn-src}")
        (final.lib.cmakeBool "BUILD_TESTS" false)
      ];

    doCheck = false;
  });

  heichips-udev-check = final.writeShellApplication {
    name = "heichips-udev-check";
    runtimeInputs = [ final.gnugrep ];
    text = ''
      if grep -rlsE 'idProduct\}=="c0ca"' \
        /etc/udev/rules.d /usr/lib/udev/rules.d /lib/udev/rules.d 2>/dev/null | grep -q .; then
        echo 1
        exit 0
      fi

      echo 0
      cat >&2 <<EOF
      warning: no udev rules for the JTAG probe; openFPGALoader will need root.
        sudo cp "''${PRJ_ROOT:-.}/nix/udev/99-openfpgaloader.rules" /etc/udev/rules.d/
        sudo udevadm control --reload-rules && sudo udevadm trigger
        then replug the probe (you also need to be in the plugdev group)
      EOF
    '';
  };

  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
    (pyfinal: pyprev: {
      nortl = pyfinal.callPackage ./nortl.nix { };
    })
  ];
}
