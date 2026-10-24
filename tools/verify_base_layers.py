"""Compare uncompressed layer identities to the mandated public registry config.

BuildKit can build FROM an image without assigning that base a local Docker tag.
Reading the registry config avoids requiring an unnecessary full base-image pull.
"""
import argparse
import json
import subprocess
import urllib.request
from urllib.parse import urlencode

BASE_REPO='rocm/pytorch'
BASE_TAG='rocm10.0_ubuntu26.04_py3.14_pytorch_release_2.13.0'


def check_layers(base,child):
    if not base or child[:len(base)]!=base:raise ValueError('Required base layers were altered, flattened, or omitted')
    return True


def registry_base_layers():
    query=urlencode({'service':'registry.docker.io','scope':'repository:'+BASE_REPO+':pull'})
    with urllib.request.urlopen('https://auth.docker.io/token?'+query,timeout=30) as r:token=json.load(r)['token']
    headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.manifest.v1+json'}
    origin='https://registry-1.docker.io/v2/'+BASE_REPO
    with urllib.request.urlopen(urllib.request.Request(origin+'/manifests/'+BASE_TAG,headers=headers),timeout=30) as r:manifest=json.load(r)
    digest=manifest['config']['digest']
    with urllib.request.urlopen(urllib.request.Request(origin+'/blobs/'+digest,headers=headers),timeout=30) as r:config=json.load(r)
    return config['rootfs']['diff_ids']


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--image',required=True);args=parser.parse_args()
    base=registry_base_layers();child=json.loads(subprocess.check_output(['docker','image','inspect',args.image,'--format','{{json .RootFS.Layers}}'],text=True))
    check_layers(base,child);print('Required base layer identities preserved:',len(base),'base layers;',len(child)-len(base),'application layers')

if __name__=='__main__':main()
