#!/usr/bin/python
"""Script to turn help files into a README.md"""

import fygen_help

def make_toc_link(section):
  return '#%s' % section.lower().replace(' ', '-')

def main():
  """Main function."""
  with open('README.md', 'w') as fout:
    fout.write('# Table of Contents\n\n')
    for section in fygen_help.SECTIONS:
      fout.write('  - [%s](%s)\n' % (section, make_toc_link(section)))
    fout.write('\n')

    for section_idx in range(len(fygen_help.SECTIONS)):
      fygen_help.help(
          section=section_idx,
          device=None,
          fout=fout,
          show_other_sections=False,
          markdown_format=True)

if __name__ == '__main__':
  main()
