#!/usr/bin/env python3
import json
import re
from common import ROOT, configuration

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')

def main():
    env = configuration()

    public = env['PUBLIC_HOST']
    editor = env['EDITOR_HOST']
    grafana_host = env.get('GRAFANA_HOST', f'grafana.{public}')

    for host in (public, editor, grafana_host):
        if (
            not re.fullmatch(
                r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?',
                host,
            )
            or '..' in host
        ):
            raise SystemExit(
                'Use DNS hostnames without schemes, paths, or ports.'
            )

    if len({public, editor, grafana_host}) != 3:
        raise SystemExit(
            'Public, editor, and Grafana hostnames must be distinct.'
        )

    runtime = ROOT / 'runtime'

    # Only public HTML gets the strict public-site CSP.
    middleware = {
        'origin-https': {
            'headers': {
                'customRequestHeaders': {
                    'X-Forwarded-Proto': 'https',
                }
            }
        },
        'public-security': {
            'headers': {
                'contentTypeNosniff': True,
                'referrerPolicy': 'strict-origin-when-cross-origin',
                'contentSecurityPolicy': (
                    "default-src 'self'; "
                    "script-src 'self'; "
                    "style-src 'self'; "
                    "img-src 'self' data:; "
                    "font-src 'self'; "
                    "connect-src 'self'; "
                    "object-src 'none'; "
                    "base-uri 'self'; "
                    "frame-ancestors 'self'; "
                    "form-action 'self'"
                ),
            }
        },
        'compressed': {
            'compress': {},
        },
        'archive-limit': {
            'rateLimit': {
                'average': 25,
                'burst': 75,
                'sourceCriterion': {
                    'requestHost': True,
                },
            }
        },
    }

    routers = {
        'publication': {
            'rule': f'Host(`{public}`)',
            'entryPoints': ['web'],
            'service': 'django',
            'middlewares': [
                'origin-https',
                'public-security',
                'compressed',
            ],
            'priority': 10,
        },
        'archive-api': {
            'rule': f'Host(`{public}`) && PathPrefix(`/api/`)',
            'entryPoints': ['web'],
            'service': 'django',
            'middlewares': [
                'origin-https',
                'public-security',
                'archive-limit',
                'compressed',
            ],
            'priority': 20,
        },
        'editor': {
            'rule': f'Host(`{editor}`)',
            'entryPoints': ['web'],
            'service': 'django',
            'middlewares': [
                'origin-https',
                'compressed',
            ],
            'priority': 10,
        },
        'grafana': {
            'rule': f'Host(`{grafana_host}`)',
            'entryPoints': ['web'],
            'service': 'grafana',
            'middlewares': [
                'origin-https',
                'compressed',
            ],
            'priority': 10,
        },
    }

    services = {
        'django': {
            'loadBalancer': {
                'servers': [
                    {'url': 'http://web:8000'},
                ],
                'passHostHeader': True,
            }
        },
        'grafana': {
            'loadBalancer': {
                'servers': [
                    {'url': 'http://grafana:3000'},
                ],
                'passHostHeader': True,
            }
        },
    }

    identity_host = env.get('KEYCLOAK_HOST', '')

    if identity_host:
        if (
            not re.fullmatch(
                r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?',
                identity_host,
            )
            or '..' in identity_host
            or identity_host in {public, editor, grafana_host}
        ):
            raise SystemExit(
                'Use a separate DNS hostname for Keycloak, '
                'without a scheme or path.'
            )

        routers['identity'] = {
            'rule': f'Host(`{identity_host}`)',
            'entryPoints': ['web'],
            'service': 'keycloak',
            'middlewares': ['origin-https'],
        }

        services['keycloak'] = {
            'loadBalancer': {
                'servers': [
                    {'url': 'http://keycloak:8080'},
                ],
                'passHostHeader': True,
            }
        }

    write(
        runtime / 'traefik-dynamic.yml',
        {
            'http': {
                'routers': routers,
                'middlewares': middleware,
                'services': services,
            }
        },
    )

    modules = {
        'http_origin': {'prober': 'http', 'timeout': '5s', 'http': {'method': 'GET', 'preferred_ip_protocol': 'ip4', 'headers': {'Host': public}}},
        'http_public_tls': {'prober': 'http', 'timeout': '10s', 'http': {'method': 'GET', 'preferred_ip_protocol': 'ip4', 'fail_if_not_ssl': True}},
        'http_ready': {'prober': 'http', 'timeout': '5s', 'http': {'preferred_ip_protocol': 'ip4'}},
    }
    write(runtime/'blackbox.yml', {'modules': modules})
    jobs=[]
    for job, address, path in [
        ('prometheus','prometheus:9090','/metrics'), ('alertmanager','alertmanager:9093','/metrics'), ('django','web:8000','/metrics/'),
        ('traefik','traefik:8082','/metrics'), ('postgres','postgres-exporter:9187','/metrics'),
        ('redis','redis-exporter:9121','/metrics'), ('node','node-exporter:9100','/metrics'),
        ('cadvisor','cadvisor:8080','/metrics'), ('loki','loki:3100','/metrics'),
        ('alloy','alloy:12345','/metrics'), ('grafana','grafana:3000','/metrics'),
        ('blackbox','blackbox-exporter:9115','/metrics'),
    ]:
        jobs.append({'job_name': job, 'metrics_path': path, 'static_configs': [{'targets': [address]}]})
    # Tunnel targets intentionally remain visible as down in local-only mode.
    jobs.append({'job_name': 'cloudflared', 'static_configs': [{'targets': ['cloudflared:2000']}]})
    for name, module, targets in [
        ('origin', 'http_origin', ['http://traefik:8080/ready/']),
        ('public', 'http_public_tls', [f'https://{public}/health/']),
        ('tunnel', 'http_ready', ['http://cloudflared:2000/ready']),
    ]:
        jobs.append({'job_name': 'probe-'+name, 'metrics_path': '/probe', 'params': {'module': [module]},
            'static_configs': [{'targets': targets}], 'relabel_configs': [
                {'source_labels': ['__address__'], 'target_label': '__param_target'},
                {'source_labels': ['__param_target'], 'target_label': 'instance'},
                {'target_label': '__address__', 'replacement': 'blackbox-exporter:9115'},
            ]})
    write(runtime/'prometheus.yml', {'global': {'scrape_interval': '30s', 'evaluation_interval': '30s',
          'external_labels': {'stack': env.get('COMPOSE_PROJECT_NAME','liberty_research')}},
          'rule_files': ['/etc/prometheus/rules.yml'], 'alerting': {'alertmanagers': [{'static_configs': [{'targets': ['alertmanager:9093']}]}]}, 'scrape_configs': jobs})
    panels=[]
    specs=[('Requests per second','sum(rate(liberty_http_requests_total[5m]))'),
           ('HTTP p95 seconds','histogram_quantile(0.95, sum by (le) (rate(liberty_http_request_duration_seconds_bucket[5m])))'),
           ('Origin and edge probes','probe_success'), ('Exporter health','up'),
           ('Host memory used','1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes'),
           ('Container memory','container_memory_working_set_bytes{container_label_com_docker_compose_service!=""}'),
           ('PostgreSQL availability','pg_up'), ('Redis memory bytes','redis_memory_used_bytes'),
           ('Publishing heartbeat age','time() - liberty_scheduler_last_success_timestamp_seconds')]
    for i, (title, expression) in enumerate(specs):
        panels.append({'id': i+1, 'type': 'timeseries', 'title': title, 'datasource': {'type':'prometheus','uid':'prometheus'},
            'gridPos': {'h':8,'w':8,'x':(i%3)*8,'y':(i//3)*8},
            'targets':[{'refId':'A','expr':expression,'legendFormat':'{{instance}} {{service}}'}]})
    panels.append({'id':10,'type':'logs','title':'Container logs','datasource':{'type':'loki','uid':'loki'},
        'gridPos':{'h':10,'w':24,'x':0,'y':24},'targets':[{'refId':'A','expr':'{service=~".+"}'}]})
    write(runtime/'dashboards/liberty.json', {'uid':'liberty-overview','title':'The Liberty Articulator',
        'schemaVersion':39,'version':1,'refresh':'30s','time':{'from':'now-1h','to':'now'},'panels':panels})
    print('Traefik, probe, scrape, and dashboard configurations generated without secret values.')

if __name__ == '__main__':
    main()
