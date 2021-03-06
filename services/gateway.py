# -*- coding: utf-8 -*-

'''

Services Dispatch

Used for dispatching URLs that are part of AppTools/ProtoRPC-based remote
API services.

-sam (<sam@momentum.io>)

'''

# Basic Imports
import config
import webapp2

# ProtoRPC Imports
from protorpc import registry
from protorpc.webapp import forms
from protorpc.webapp import service_handlers

# AppTools Imports
from apptools.services import RemoteServiceHandlerFactory


def _normalize_services(mixed_services):

    ''' _normalize_services - borrowed from webapp2. '''

    if isinstance(mixed_services, dict):
        mixed_services = mixed_services.iteritems()

    services = []
    for service_item in mixed_services:
        if isinstance(service_item, (list, tuple)):
            path, service = service_item
        else:
            path = None
            service = service_item

        if isinstance(service, basestring):
            # Lazily import the service class.
            service = webapp2.import_string(service)

        services.append((path, service))

    return services


def generateServiceMappings(svc_cfg, registry_path=forms.DEFAULT_REGISTRY_PATH):

    ''' Utility function that reads the services config and generates URL mappings to service classes. '''

    services = []

    ## Generate service mappings in tuple(<invocation_url>, <classpath>) format
    for service, cfg in svc_cfg['services'].items():
        if cfg['enabled'] == True:
            services.append(('/'.join(svc_cfg['config']['url_prefix'].split('/') + [service]), cfg['service']))

    services = _normalize_services(services)
    mapping = []
    registry_map = {}

    if registry_path is not None:
        registry_service = registry.RegistryService.new_factory(registry_map)
        services = list(services) + [(registry_path, registry_service)]
        forms_handler = forms.FormsHandler(registry_path=registry_path)
        mapping.append((registry_path + r'/form(?:/)?', forms_handler))
        mapping.append((registry_path + r'/form/(.+)', forms.ResourceHandler))

    paths = set()
    for path, service in services:
        service_class = getattr(service, 'service_class', service)
        if not path:
            path = '/' + service_class.definition_name().replace('.', '/')

        if path in paths:
            raise service_handlers.ServiceConfigurationError(
                'Path %r is already defined in service mapping'
                % path.encode('utf-8'))
        else:
            paths.add(path)

        # Create service mapping for webapp2.
        new_mapping = RemoteServiceHandlerFactory.default(service).mapping(path)
        mapping.append(new_mapping)

        # Update registry with service class.
        registry_map[path] = service_class

    return mapping


_application = webapp2.WSGIApplication(generateServiceMappings(config.config.get('apptools.project.services')), debug=config.debug, config=config.config)


if __name__ == '__main__':
    _application.run()
