import gzip,hashlib,importlib.util,io,subprocess,tarfile,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('source_release_under_test',ROOT/'tools/source_release.py')
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)


class SourceReleaseTests(unittest.TestCase):
    def git(self,root,*args):
        return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.DEVNULL)
    def repo(self,extra=None,*,tag=True,on_main=True):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name).resolve()
        self.git(root,'init','-b','main');self.git(root,'config','user.name','Release fixture')
        self.git(root,'config','user.email','release@example.invalid')
        for name,value in {'pyproject.toml':'[project]\nname="release-fixture"\nversion="0.1.0"\n',
                           'LICENSE':'Apache-2.0 fixture\n','README.md':'Public source\n',
                           '.gitignore':'dist/\n.env\nsecrets/\n'}.items():
            (root/name).write_text(value)
        for name,value in (extra or {}).items():
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
            if value is None:path.symlink_to(root/'README.md')
            else:path.write_bytes(value)
        self.git(root,'add','--force','.');self.git(root,'commit','-m','fixture source')
        self.git(root,'update-ref','refs/remotes/origin/main','HEAD')
        if not on_main:
            (root/'README.md').write_text('Unmerged source\n');self.git(root,'add','README.md')
            self.git(root,'commit','-m','unmerged fixture')
        if tag:self.git(root,'tag','v0.1.0')
        return root

    def test_archives_tagged_clean_main_source_and_checksum_reproducibly(self):
        root=self.repo();(root/'.env').write_text('local ignored secret')
        one=release.create_release(root,'v0.1.0',root/'dist/one')
        two=release.create_release(root,'v0.1.0',root/'dist/two')
        self.assertEqual(one.read_bytes(),two.read_bytes())
        self.assertEqual(one.name,'release-fixture-0.1.0-source.tar.gz')
        self.assertEqual((one.parent/'SHA256SUMS').read_text(),hashlib.sha256(one.read_bytes()).hexdigest()+'  '+one.name+'\n')
        with tarfile.open(fileobj=io.BytesIO(gzip.decompress(one.read_bytes())),mode='r:') as archive:
            names=archive.getnames()
            self.assertIn('release-fixture-0.1.0/LICENSE',names)
            self.assertTrue(all(n=='release-fixture-0.1.0' or n.startswith('release-fixture-0.1.0/') for n in names))
            self.assertFalse(any('/.git/' in n or n.endswith('/.env') for n in names))

    def test_version_tag_head_main_and_clean_checkout_are_required(self):
        for tag in ('v0.2.0','0.1.0','v01.1.0','v0.1.0;bad','../v0.1.0'):
            with self.subTest(tag=tag),self.assertRaises(ValueError):release.create_release(self.repo(),tag,Path('/tmp/unused'))
        with self.assertRaises(ValueError):
            root=self.repo(tag=False);release.create_release(root,'v0.1.0',root/'dist/release')
        root=self.repo();(root/'README.md').write_text('dirty')
        with self.assertRaises(ValueError):release.create_release(root,'v0.1.0',root/'dist/release')
        root=self.repo();(root/'extra.txt').write_text('new');self.git(root,'add','extra.txt');self.git(root,'commit','-m','later')
        with self.assertRaises(ValueError):release.create_release(root,'v0.1.0',root/'dist/release')
        root=self.repo(on_main=False)
        with self.assertRaises(ValueError):release.create_release(root,'v0.1.0',root/'dist/release')

    def test_tracked_private_files_binaries_symlinks_and_credentials_are_rejected(self):
        files={'.env':b'not a real credential','secrets/network.json':b'{}','build/app.labapp':b'package',
               'firmware.bin':b'firmware','recording.wav':b'voice','app/desk_key.h':b'private fixture',
               'alias.py':None,'odd'+chr(92)+'name.py':b'source','leak.txt':('gh'+'p_'+'a'*40).encode(),
               'private-path.txt':('/Users'+'/example/private').encode()}
        for name,value in files.items():
            root=self.repo({name:value})
            with self.subTest(name=name),self.assertRaises(ValueError):
                release.create_release(root,'v0.1.0',root/'dist/release')
            self.assertFalse((root/'dist/release').exists())

    def test_output_cannot_escape_dist_follow_symlinks_or_overwrite(self):
        root=self.repo();outside=root/'outside';outside.mkdir();(root/'dist').mkdir()
        (root/'dist/link').symlink_to(outside,target_is_directory=True)
        for output in (outside,root/'dist/link/result',root/'dist/../outside/result'):
            with self.subTest(output=output),self.assertRaises(ValueError):release.create_release(root,'v0.1.0',output)
        target=release.create_release(root,'v0.1.0',root/'dist/release')
        with self.assertRaises(ValueError):release.create_release(root,'v0.1.0',target.parent)
        self.assertTrue(target.is_file())

    def test_release_workflow_runs_full_ci_before_source_only_publication(self):
        workflow=(ROOT/'.github/workflows/release.yml').read_text()
        self.assertIn("tags: ['v*']",workflow);self.assertIn('needs: verify',workflow)
        self.assertIn('uses: ./.github/workflows/tests.yml',workflow)
        self.assertIn('workflow_call:',(ROOT/'.github/workflows/tests.yml').read_text())
        for text in ('persist-credentials: false','contents: read','contents: write','fetch-depth: 0',
                     'git merge-base --is-ancestor HEAD origin/main','--verify-tag','--tag "$RELEASE_TAG"'):
            self.assertIn(text,workflow)
        self.assertNotIn('continue-on-error',workflow);self.assertNotIn('--clobber',workflow)
        self.assertIn('source-release/*',workflow)
