import json

from django.conf import settings

import fudge
from funfactory.urlresolvers import reverse
import jwt
from nose.tools import eq_
import test_utils

from rockit.music.models import Track, TrackFile
from rockit.sync.tests import create_audio_file


class TestIndex(test_utils.TestCase):

    def setUp(self):
        self.af = create_audio_file(make_mp3=True,
                                    make_ogg=True)

    def get(self, client_id=None, secret=None, extra_req=None):
        if not client_id:
            client_id = settings.API_CLIENTS.keys()[0]
        if not secret:
            secret = settings.API_CLIENTS[client_id]
        req = dict(email='edna@wat.com')
        if extra_req:
            req.update(extra_req)
        req = {'iss': client_id,
               'aud': settings.SITE_URL,
               'request': req}
        return self.client.get(reverse('music.index'),
                               dict(r=jwt.encode(req, secret)))

    @fudge.patch('rockit.music.models.s3')
    def test_success(self, s3):
        s3.expects('get_authenticated_url').returns('<s3 url>')
        resp = self.get()
        eq_(resp.status_code, 200)
        data = json.loads(resp.content)
        eq_(data['tracks'][0]['id'], self.af.id)
        eq_(data['tracks'][0]['artist'], 'Gescom')
        eq_(data['tracks'][0]['album'], 'Minidisc')
        eq_(data['tracks'][0]['track'], 'Horse')
        eq_(data['tracks'][0]['s3_urls']['mp3'], '<s3 url>')
        eq_(data['tracks'][0]['s3_urls']['ogg'], '<s3 url>')

    @fudge.patch('rockit.music.models.s3')
    def test_ignore_inactive_tracks(self, s3):
        s3.provides('get_authenticated_url').returns('<s3 url>')
        Track.objects.all().update(is_active=False)
        resp = self.get()
        eq_(resp.status_code, 200)
        data = json.loads(resp.content)
        eq_(data['tracks'], [])

    @fudge.patch('rockit.music.models.s3')
    def test_ignore_inactive_files(self, s3):
        s3.provides('get_authenticated_url').returns('<s3 url>')
        TrackFile.objects.all().update(is_active=False)
        resp = self.get()
        eq_(resp.status_code, 200)
        data = json.loads(resp.content)
        eq_(data['tracks'], [])

    @fudge.patch('rockit.music.models.s3')
    def test_ignore_deleted_files(self, s3):
        s3.provides('get_authenticated_url').returns('<s3 url>')
        TrackFile.objects.all().delete()
        resp = self.get()
        eq_(resp.status_code, 200)
        data = json.loads(resp.content)
        eq_(data['tracks'], [])

    @fudge.patch('rockit.music.models.s3')
    def test_unauthorized(self, s3):
        resp = self.get(secret='invalid')
        eq_(resp.status_code, 403)

    @fudge.patch('rockit.music.models.s3')
    def test_files_not_processed(self, s3):
        TrackFile.objects.all().delete()
        resp = self.get()
        eq_(resp.status_code, 200)
        data = json.loads(resp.content)
        eq_(data['tracks'], [])

    @fudge.patch('rockit.music.models.s3')
    def test_page_size(self, s3):
        s3.expects('get_authenticated_url').returns('<s3 url>')
        create_audio_file(make_mp3=True,
                          make_ogg=True,
                          artist='Aphex Twin')
        resp = self.get(extra_req={'page_size': 1})
        eq_(resp.status_code, 200)
        data = json.loads(resp.content)
        eq_([d['artist'] for d in data['tracks']], ['Gescom'])

    @fudge.patch('rockit.music.models.s3')
    def test_page_offset(self, s3):
        s3.expects('get_authenticated_url').returns('<s3 url>')
        create_audio_file(make_mp3=True,
                          make_ogg=True,
                          artist='Aphex Twin')
        resp = self.get(extra_req={'page_size': 2,
                                   'offset': 1})
        eq_(resp.status_code, 200)
        data = json.loads(resp.content)
        eq_([d['artist'] for d in data['tracks']], ['Aphex Twin'])
