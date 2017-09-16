# -*- coding: UTF-8 -*-
"""
This module contains functions that parse stdout of a CLI command into a usable
Python data structure.
"""


def ifconfig_to_dict(ifconfig_output):
    """Parse the output from the command `ifconfig` into a dictionary

    :Returns: Dictionary

    :param ifconfig_output: **Required** The pile of stuff outputted by running `ifconfig`
    :type ifconfig_output: String
    """
    base = {'interfaces' : {}}

    iface_name = None
    for line in ifconfig_output.split('\n'):
        if line and not line.startswith(' '):
            # It's the start of a new interface
            chunks = line.split()

            iface_name = chunks[0].strip()
            iface = base['interfaces'].setdefault(iface_name, {})
            iface['link'] = chunks[2].strip()
            iface['hwaddr'] = None
            iface['ipv4'] = {}
            iface['ipv6'] = {}
            iface['flags'] = None,
            iface['mtu'] = None,
            iface['metric'] = None
            iface['rx packets'] = {}
            iface['tx packets'] = {}
            iface['collisions'] = None,
            iface['txqueuelen'] = None,
            iface['rx bytes'] = {}
            iface['tx bytes'] = {}
            if 'hwaddr' in chunks[3].lower():
                iface['hwaddr'] = chunks[4]
            else:
                iface['hwaddr'] = 'Loopback'

        elif line.startswith(' ') and iface_name:
            # keep parsing the interface info
            chunks = line.split()
            if chunks[0] == 'inet':
                ip = chunks[1].split(':')[1]
                bcast = chunks[2].split(':')[1]
                mask = chunks[-1].split(':')[1]
                if bcast == mask:
                    # it's loopback
                    base['interfaces'][iface_name]['ipv4'][ip] = {'mask': mask}
                else:
                    base['interfaces'][iface_name]['ipv4'][ip] = {'bcast': bcast, 'mask': mask}
                continue

            elif chunks[0] == 'inet6':
                ip6 = chunks[2]
                scope = chunks[3].split(':')[1]
                base['interfaces'][iface_name]['ipv6'][ip6] = {'scope' : scope}
                continue

            elif 'Metric' in chunks[-1]:
                metric = int(chunks.pop(-1).split(':')[1])
                mtu = int(chunks.pop(-1).split(':')[1])
                flags = ' '.join(chunks)
                base['interfaces'][iface_name]['mtu'] = mtu
                base['interfaces'][iface_name]['metric'] = metric
                base['interfaces'][iface_name]['flags'] = flags
                continue

            elif 'RX' == chunks[0] and 'packets' in chunks[1]:
                packets = int(chunks[1].split(':')[1])
                errors = int(chunks[2].split(':')[1])
                dropped = int(chunks[3].split(':')[1])
                overruns = int(chunks[4].split(':')[1])
                frame = int(chunks[5].split(':')[1])
                base['interfaces'][iface_name]['rx packets'] = {'packets': packets,
                                                           'errors': errors,
                                                           'dropped': dropped,
                                                           'overruns': overruns,
                                                           'frame' : frame}
                continue

            elif 'TX' == chunks[0] and 'packets' in chunks[1]:
                packets = int(chunks[1].split(':')[1])
                errors = int(chunks[2].split(':')[1])
                dropped = int(chunks[3].split(':')[1])
                overruns = int(chunks[4].split(':')[1])
                carrier = int(chunks[5].split(':')[1])
                base['interfaces'][iface_name]['tx packets'] = {'packets': packets,
                                                           'errors': errors,
                                                           'dropped': dropped,
                                                           'overruns': overruns,
                                                           'frame' : frame}
                continue

            elif 'collisions' in chunks[0]:
                collisions = int(chunks[0].split(':')[1])
                txqueuelen = int(chunks[1].split(':')[1])
                base['interfaces'][iface_name]['collisions'] = collisions
                base['interfaces'][iface_name]['txqueuelen'] = txqueuelen
                continue

            elif 'RX' ==  chunks[0] and 'bytes' in chunks[1]:
                r_bytes = int(chunks[1].split(':')[1])
                t_bytes = int(chunks[5].split(':')[1])
                base['interfaces'][iface_name]['rx bytes'] = r_bytes
                base['interfaces'][iface_name]['tx bytes'] = t_bytes
                continue
        else:
            # empty line between interfaces
            continue
    return base


def memory_to_dict(output):
    """Parse the output from the command `free -m` into a dictionary

    :Returns: Dictionary

    :param output: **Required** The pile of stuff outputted by running `free -m`
    :type output: String
    """
    lines = output.split('\n')
    the_keys = lines[0].split()
    memory_values = [int(x) for x in lines[1].split() if not x.startswith('M')]
    swap_values = [int(x) for x in lines[3].split() if not x.startswith('S')]

    memory = dict(zip(the_keys, memory_values))
    swap = dict(zip(the_keys, swap_values))
    return {'memory' : {'ram': memory, 'swap': swap}}


def df_to_dict(output):
    """Parse the output from the command `df` into a dictionary

    :Returns: Dictionary

    :param output: **Required** The pile of stuff outputted by running `df`
    :type output: String
    """
    response = {'filesystems': {}}
    lines = output.split('\n')
    lines.pop(0) # pop the header
    lines.pop(-1) # remove empty string from end; result of spliting on lines...
    for idx, line in enumerate(lines):
        data = line.split()
        filesystem = data[0]
        oneK_blocks = data[1]
        used = data[2]
        available = data[3]
        used_percent = data[4]
        mounted_on = data[5]
        response['filesystems'][filesystem] = {
            '1K-blocks' : oneK_blocks,
            'used' : used,
            'available' : available,
            'used percent' : used_percent,
            'mounted on' : mounted_on
            }
    return response
