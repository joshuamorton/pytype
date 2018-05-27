"""Utilities for dealing with project configuration."""

import os
from six.moves import configparser


def find_config_file(path, filename='setup.cfg'):
  """Finds the first instance of filename in a prefix of path."""

  # Make sure path is a directory
  if not os.path.isdir(path):
    path = os.path.dirname(path)

  # Guard against symlink loops and /
  seen = set()
  while path and path not in seen:
    seen.add(path)
    f = os.path.join(path, filename)
    if os.path.exists(f) and os.path.isfile(f):
      return f
    path = os.path.dirname(path)

  return None


class ConfigSection(object):
  """Read a given set of keys from a section of a config file."""

  def __init__(self, parser, section, keymap):
    self.parser = parser
    self.section = section
    self.keymap = keymap

  @classmethod
  def create_from_file(cls, filepath, section, keymap):
    """Create a ConfigSection if the file at filepath has section."""
    parser = configparser.ConfigParser()
    try:
      parser.read(filepath)
    except configparser.MissingSectionHeaderError:
      # We've read an improperly formatted config file.
      return None
    if parser.has_section(section):
      return cls(parser, section, keymap)
    return None

  def get(self, key):
    """Get the value for the given key."""
    try:
      # The 'fallback' option is Python 3-only, so we use a try/except.
      value = self.parser.get(self.section, key)
    except configparser.NoOptionError:
      return None
    converter = self.keymap[key]
    if converter:
      value = converter(value)
    return value
