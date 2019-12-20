#!/usr/bin/env python3.8

# Turn a pass (https://www.passwordstore.org/) repository into an XML file to import into KeePassXC. XML is dumped into stdout.
#
# Usage:
# python3 pass-to-keepassxc.py <password store directory>
#
# Example:
#
# Typically, pass's password store directory is `~/.password-store`.
#
# $ python3 pass-to-keepassxc.py ~/.password-store > deleteme.xml
# $ keepassxc-cli import deleteme.xml MyKeepassXCPasswords.kbdx
# $ rm deleteme.xml
#
# Then go and configure additional settings in the KeePassXC GUI or CLI.

from xml.etree import ElementTree as ET
from xml.dom import minidom
import sys
import argparse
import re
import subprocess
from pathlib import PurePosixPath, Path
import os
from typing import List

class KeepassXCEntry:
    """
    Generate XML entries like this:
        <Entry>
                <String>
                        <Key>Notes</Key>
                        <Value ProtectInMemory="True"></Value>
                </String>
                <String>
                        <Key>Password</Key>
                        <Value ProtectInMemory="True"></Value>
                </String>
                <String>
                        <Key>Title</Key>
                        <Value></Value>
                </String>
                <String>
                        <Key>URL</Key>
                        <Value></Value>
                </String>
                <String>
                        <Key>UserName</Key>
                        <Value></Value>
                </String>
                <AutoType>
                        <Enabled>True</Enabled>
                        <DataTransferObfuscation>0</DataTransferObfuscation>
                        <DefaultSequence/>
                </AutoType>
                <History/>
        </Entry>
    """


    def __init__(self, username, password, url, title, notes=''):
        self.root = ET.Element('Entry')
        self.add_string_field('Notes', notes)
        self.add_string_field('UserName', username)
        self.add_string_field('Password', password)
        self.add_string_field('URL', url)
        self.add_string_field('Title', title)
        self.add_auto_type()
        

    def __str__(self):
        return ET.tostring(self.root, encoding='utf-8')
    

    def add_string_field(self, k, v):
        string = ET.SubElement(self.root, 'String')
        key = ET.SubElement(string, 'Key')
        key.text = k
        value = ET.SubElement(string, 'Value')
        value.text = v
        value.set('ProtectInMemory', 'True')
        return self


    def add_auto_type(self):
        autotype = ET.SubElement(self.root, 'AutoType');
        enabled = ET.SubElement(autotype, 'Enabled');
        enabled.text = 'True';
        dto = ET.SubElement(autotype, 'DataTransferObfuscation');
        dto.text = '0';
        ds = ET.SubElement(autotype, 'DefaultSequence');
        return self
        

class KeepassXCDump:
    """
    Entire file:
    
    <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <KeePassFile>
      <Root>
        <Group>
                <Name>{group name}</Name>
                [<Entry>...</Entry>...]
        </Group>
      </Root>
    </KeePassFile>
    """

    def __init__(self):
        self.KeePassFile = ET.Element('KeePassFile')
        Root = ET.SubElement(self.KeePassFile, 'Root')
        self.root = ET.SubElement(Root, 'Group')
        root_name = ET.SubElement(self.root, 'Name')
        root_name.text = 'Root'
    
    
    def add_group(self, name, entries: List[KeepassXCEntry]):
        group_root = ET.SubElement(self.root, 'Group')
        group_name = ET.SubElement(group_root, 'Name')
        group_name.text = name
        group_root.extend(map(lambda x: x.root, entries))


    def __str__(self):
        return ET.tostring(self.KeePassFile, encoding='unicode')
        

class KeepassXCGroup:
    def __init__(self, group_name):
        self.root = ET.Element('Group')
        name = ET.SubElement(self.root, 'Name')
        name.text = group_name;


    def add_entry(entry: KeepassXCEntry):
        self.root.append(entry)


def parse_pass_format(src: str):
    it = src.split('\n')
    password = it[0]
    notes = '\n'.join(it[1:])
    return (password, notes)


def find_files(directory: Path):
    for node in (x for x in directory.iterdir() if x.name[0] != '.'):
        if node.is_dir():
            yield from find_files(Path(node))
        elif node.is_file():
            yield Path(node)


def decrypt(gpg_encrypted_file: Path):
    out = subprocess.run(["gpg", "--quiet", "--decrypt", gpg_encrypted_file.resolve()], capture_output=True)
    return out.stdout.decode('utf-8')


if __name__ == '__main__':
    if len(sys.argv) < 1:
        sys.exit(1)
    password_store_dir = Path(sys.argv[1])
    out = KeepassXCDump()
    # treat a subdirectory as a keeepassxc 'group'
    for group in (x for x in password_store_dir.iterdir() if x.is_dir() and x.name[0] != '.'):
        keepassxc_entries: List[KeepassXCEntry] = []
        for entry in find_files(group):
            url = f"https://{entry.parent.name}"
            username = re.split(r'\..*?$', entry.name)[0]
            try:
                file_contents = decrypt(entry)
            except UnicodeDecodeError:
                # not UTF-8; skip it
                continue
            password, notes = parse_pass_format(file_contents)
            keepassxc_entries.append(KeepassXCEntry(username=username, password=password, url=url, title=username, notes=notes))
        out.add_group(group.name, keepassxc_entries)
    print(out)
    sys.exit(0)
