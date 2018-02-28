class Converter:
    def to_script(self, entries, head='#! /usr/bin/env bash\nset -e\n'):
        return head+'\n'.join(self.commands(entries))+'\n'
