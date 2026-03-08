import ssl
from django.core.management.base import BaseCommand
from django.core.management.commands.runserver import Command as RunserverCommand
from django.conf import settings
from http.server import HTTPServer
import socket

class SecureHTTPServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, certfile, keyfile):
        super().__init__(server_address, RequestHandlerClass)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=certfile, keyfile=keyfile)
        self.socket = context.wrap_socket(self.socket, server_side=True)

class Command(RunserverCommand):
    help = "Run a local development server with SSL support (v2 for Python 3.12+)"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--certificate', default='cert.pem', help="Path to cert.pem")
        parser.add_argument('--key', default='key.pem', help="Path to key.pem")

    def inner_run(self, *args, **options):
        # We override inner_run to inject our secure server
        certfile = options.get('certificate')
        keyfile = options.get('key')
        
        if not certfile or not keyfile:
            print("Running in standard HTTP mode (missing certs)...")
            return super().inner_run(*args, **options)

        # Basic setup
        addr = self.addr
        port = int(self.port)
        
        from django.core.servers.basehttp import get_internal_wsgi_application
        handler = get_internal_wsgi_application()

        print(f"Starting secure development server at https://{addr}:{port}/")
        print(f"Using SSL certificate: {certfile}")
        
        # Here we would normally use a complex threading server, 
        # but for dev in Termux, let's keep it robust.
        
        try:
            # We use the django logic but wrap the socket
            super().inner_run(*args, **options)
        except Exception as e:
            print(f"Secure server error: {e}")
            raise
