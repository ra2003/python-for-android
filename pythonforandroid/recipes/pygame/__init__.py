
from pythonforandroid.toolchain import Recipe, shprint, ArchARM, current_directory, debug, info, ensure_dir
from os.path import exists, join
import sh
import glob

class PygameRecipe(Recipe):
    name = 'pygame'
    version = '1.9.1'
    url = 'http://pygame.org/ftp/pygame-{version}release.tar.gz'

    depends = ['python2', 'sdl']
    conflicts = ['sdl2']

    def get_recipe_env(self, arch):
        env = super(PygameRecipe, self).get_recipe_env(arch)
        env['LDFLAGS'] = env['LDFLAGS'] + ' -L{}'.format(
            self.ctx.get_libs_dir(arch.arch))
        env['LDSHARED'] = join(self.ctx.root_dir, 'tools', 'liblink')
        env['LIBLINK'] = 'NOTNONE'
        env['NDKPLATFORM'] = self.ctx.ndk_platform

        # Every recipe uses its own liblink path, object files are collected and biglinked later
        liblink_path = join(self.get_build_container_dir(arch.arch), 'objects_{}'.format(self.name))
        env['LIBLINK_PATH'] = liblink_path
        ensure_dir(liblink_path)
        return env

    def prebuild_arch(self, arch):
        if exists(join(self.get_build_container_dir(arch.arch), '.patched')):
            info('Pygame already patched, skipping.')
            return
        shprint(sh.cp, join(self.get_recipe_dir(), 'Setup'),
                join(self.get_build_dir(arch.arch), 'Setup'))
        self.apply_patch(join('patches', 'fix-surface-access.patch'), arch.arch)
        self.apply_patch(join('patches', 'fix-array-surface.patch'), arch.arch)
        self.apply_patch(join('patches', 'fix-sdl-spam-log.patch'), arch.arch)
        shprint(sh.touch, join(self.get_build_container_dir(arch.arch), '.patched'))
        
    def build_arch(self, arch):
        # AND: I'm going to ignore any extra pythonrecipe or cythonrecipe behaviour for now
        
        env = self.get_recipe_env(arch)
        
        env['CFLAGS'] = env['CFLAGS'] + ' -I{jni_path}/png -I{jni_path}/jpeg'.format(
            jni_path=join(self.ctx.bootstrap.build_dir, 'jni'))
        env['CFLAGS'] = env['CFLAGS'] + ' -I{jni_path}/sdl/include -I{jni_path}/sdl_mixer'.format(
            jni_path=join(self.ctx.bootstrap.build_dir, 'jni'))
        env['CFLAGS'] = env['CFLAGS'] + ' -I{jni_path}/sdl_ttf -I{jni_path}/sdl_image'.format(
            jni_path=join(self.ctx.bootstrap.build_dir, 'jni'))
        debug('pygame cflags', env['CFLAGS'])

        
        env['LDFLAGS'] = env['LDFLAGS'] + ' -L{libs_path} -L{src_path}/obj/local/{arch} -lm -lz'.format(
            libs_path=self.ctx.libs_dir, src_path=self.ctx.bootstrap.build_dir, arch=env['ARCH'])

        env['LDSHARED'] = join(self.ctx.root_dir, 'tools', 'liblink')

        with current_directory(self.get_build_dir(arch.arch)):
            info('hostpython is ' + self.ctx.hostpython)
            hostpython = sh.Command(self.ctx.hostpython)
            shprint(hostpython, 'setup.py', 'install', '-O2', _env=env,
                    _tail=10, _critical=True)

            info('strip is ' + env['STRIP'])
            build_lib = glob.glob('./build/lib*')
            assert len(build_lib) == 1
            print('stripping pygame')
            shprint(sh.find, build_lib[0], '-name', '*.o', '-exec',
                    env['STRIP'], '{}', ';')

        python_install_path = join(self.ctx.build_dir, 'python-install')
        # AND: Should do some deleting here!
        print('Should remove pygame tests etc. here, but skipping for now')


recipe = PygameRecipe()
