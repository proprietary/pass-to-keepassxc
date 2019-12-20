# Import pass git repos into KeepassXC

Tired of using pass? Want to switch to the nice GUI and wider ecosystem of KeePassXC?

Turn a pass (https://www.passwordstore.org/) repository into an XML file to import into KeePassXC. XML is dumped into stdout.

## Usage

```bash
$ python3 pass-to-keepassxc.py <password store directory>
```

## Example

Typically, pass's password store directory is `~/.password-store`.

```bash
$ python3 pass-to-keepassxc.py ~/.password-store > deleteme.xml
$ keepassxc-cli import deleteme.xml MyKeepassXCPasswords.kbdx
$ rm deleteme.xml
```

Then go and configure additional settings in the KeePassXC GUI or CLI.

## Assumptions

- The subdirectories of `<password-store-directory>` are equivalent to "groups" in KeePassXC.
- Each leaf file (e.g., .gpg files) is a GPG-encrypted file with the first line being the password.
- The name of the directory above a leaf file is a URL of a site.
- Additional lines after the first line should be stored in the "Notes" field in KeePassXC.

This assumes a directory structure like this:

```
...
├── financial
│   ├── bank.example.com
│   │   └── dumbusername99
│   └── ...
└── browser
    ├── webmail.example.com
    │   └── alice@example.com.gpg
...
```

You may have to either edit this script or manually fix the entries in KeepassXC afterward if you are doing something different.
