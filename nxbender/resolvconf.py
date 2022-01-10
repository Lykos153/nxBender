
import logging
import subprocess

class ResolvConf(object):
    """Class which encapsulates DNS manipulation using Debian's resolvconf or openresolv"""
    def __init__(self, options):
        """Constructor

        param options The parsed command line options to the program.
        """
        self.options = options

    def SetDns(self, device:str, srv_options):
        """Called after the PPP channel connects to configure DNS using resolvconf.

        param device The name of the local network device, e.g. ppp0
        param srv_options Dict of settings passed down by the server on connect
        """
        resolv_conf_lines = []
        # header
        resolv_conf_lines.append(f'# Generated by nxBender for {device}')

        # nameserver lines
        for dns in ['dns1', 'dns2', 'dns3']:
            try:
                if srv_options[dns] != "0.0.0.0":
                    resolv_conf_lines.append(f'nameserver {srv_options[dns]}')
            except KeyError as err:
                # ignore these, because the number of DNS servers returned will vary
                pass

        # search lines
        # The server sends both "dnsSuffixes" and "dnsSuffix" with the same (single) value
        # As I don't know how to parse the former, use the latter for now.
        try:
            domain = srv_options['dnsSuffix']
            resolv_conf_lines.append(f'search {domain}')
        except KeyError as err:
                # ignore if not sent
                pass

        # pass the lot to resolvconf
        # <data> | resolvconf -a ppp0
        logging.debug("DNS settings to add:")
        for line in resolv_conf_lines:
            logging.debug(f'\t{line}')

        data = '\n'.join(resolv_conf_lines)
        args = ['resolvconf', '-a'] + [device]
        self._RunResolvConf(args, data)

    def RemoveDns(self, device:str, srv_options):
        """Called after the PPP channel disconnects to remove DNS settings using resolvconf.

        param device The name of the local network device, e.g. ppp0
        param srv_options Dict of settings passed down by the server on connect
        """
        data =""
        args = ['resolvconf', '-f', '-d'] + [device]
        self._RunResolvConf(args, data)

    def _RunResolvConf(self, args:list, input_data:str):
        """Encapsulate running the resolvconf binary.

        param args The list of arguments to pass
        param input_data The input to pipe to std input
        """
        try:
            resolvconf = subprocess.run(args,
                                         text = True,
                                         input = input_data,
                                         check = True
                                         )
        except OSError as err:
            logging.error(f"Unable to run {args[0]}: {err.strerror}")
        except subprocess.CalledProcessError as err:
            logging.error(
                f'{args[0]} exited with status {err.returncode}: {err.stdout} {err.stderr}')
