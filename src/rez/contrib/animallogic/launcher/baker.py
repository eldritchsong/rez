from rez.contrib.animallogic.launcher.mode import Mode
from rez.contrib.animallogic.launcher.operatingsystem import OperatingSystem
from rez.contrib.animallogic.launcher.settingtype import SettingType
from rez.contrib.animallogic.launcher.exceptions import BakerError
import datetime
import getpass
import logging


logger = logging.getLogger(__name__)


class Baker(object):

    def __init__(self, launcher_service, rez_service):

        self.launcher_service = launcher_service
        self.rez_service = rez_service

        self.now = datetime.datetime.now()
        self.username = getpass.getuser()
        self.mode = Mode.shell
        self.operating_system = OperatingSystem.get_current_operating_system()
        self.max_fails = -1

    def set_max_fails(self, max_fails):

        self.max_fails = max_fails

    def display_settings(self, settings):

        for setting in settings:
            logger.info("\t%s" % (setting.get_setting_as_package_request()))

    def bake(self, source, destination):

        logger.info("Retrieving settings from Launcher %s." % source)

        package_settings = self.get_package_settings_from_launcher(source)

        if not package_settings:
            raise BakerError("Unable to find package settings in %s." % source)

        logger.info("Found settings:")
        self.display_settings(package_settings)

        package_requests = self.get_package_requests_from_settings(package_settings)

        logger.info("Resolving environment for %s." % package_requests)

        resolved_package_settings = self.get_resolved_settings_from_package_requests(package_requests)

        self.display_settings(resolved_package_settings)

        logger.info("Creating new preset %s from settings." % destination)

        self.create_new_preset_from_package_settings(destination, resolved_package_settings, '')

    def get_package_settings_from_launcher(self, source):

        settings = self.launcher_service.get_settings_from_path(source, self.mode,  username=self.username, operating_system=self.operating_system, date=self.now)

        return [setting for setting in settings if setting.setting_type == SettingType.package]

    def get_package_requests_from_settings(self, settings):

        package_requests = []

        for setting in settings:
            request = setting.get_setting_as_package_request()

            if request:
                package_requests.append(request)

        return package_requests

    def get_resolved_settings_from_package_requests(self, package_requests):

        try:
            return self.rez_service.get_resolved_settings_from_requirements(package_requests, max_fails=self.max_fails)
        except Exception, e:
            raise BakerError(e)

    def create_new_preset_from_package_settings(self, destination, package_settings, description=None):

        preset = self.launcher_service.create_preset(destination, description, username=self.username)

        self.launcher_service.add_settings_to_preset(package_settings, destination, username=self.username)

        return preset