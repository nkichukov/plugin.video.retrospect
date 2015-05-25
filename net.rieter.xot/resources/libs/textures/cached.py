#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================
import hashlib
import os

from textures import TextureBase


class Cached(TextureBase):
    def __init__(self, textureUrl, cachePath, channel, logger, uriHandler):
        TextureBase.__init__(self, channel, setCdn=True, logger=logger)

        # what is the URL for the CDN?
        if textureUrl:
            self.__channelTextureUrl = "%s/%s" % (textureUrl, self._cdnSubFolder)
        else:
            self.__channelTextureUrl = "http://www.rieter.net/net.rieter.xot.cdn/%s" % (self._cdnSubFolder, )

        self.__channelTexturePath = os.path.join(cachePath, "textures", self._cdnSubFolder)
        if not os.path.isdir(self.__channelTexturePath):
            os.makedirs(self.__channelTexturePath)

        self.__uriHandler = uriHandler

    def GetTextureUri(self, fileName):
        """ Gets the full URI for the image file. Depending on the type of textures handling, it might also cache
        the texture and return that path.

        @type fileName: the file name

        """

        if os.path.isabs(fileName):
            if self._logger is not None:
                self._logger.Trace("Already cached texture found: '%s'", fileName)
            return fileName

        # Check if we already have the file
        texturePath = os.path.join(self.__channelTexturePath, fileName)
        if not os.path.isfile(texturePath):
            # Missing item. Fetch it
            uri = "%s/%s" % (self.__channelTextureUrl, fileName)

            if self._logger is not None:
                self._logger.Trace("Fetching texture '%s' from '%s'", fileName, uri)

            imageBytes = self.__uriHandler.Open(uri)
            if imageBytes:
                fs = open(texturePath, mode='wb')
                fs.write(imageBytes)
                fs.close()
            elif self._logger:
                self._logger.Error("Could not update Texture: %s", uri)

        if self._logger is not None:
            self._logger.Trace("Returning cached texture for '%s' from '%s'", fileName, texturePath)

        return texturePath

    def PurgeTextureCache(self):
        """ Removes those entries from the textures cache that are no longer required. """

        if self._logger is not None:
            self._logger.Info("Purging Texture for: %s", self._channelPath)

        # read the md5 hashes
        fp = file(os.path.join(self._channelPath, "..", "%s.md5" % (self._addonId, )))
        lines = fp.readlines()
        fp.close()

        # get a lookup table
        textures = [reversed(line.rstrip().split(" ")) for line in lines]
        # noinspection PyTypeChecker
        textures = dict(textures)

        # remove items not in the textures.md5
        images = [image for image in os.listdir(self.__channelTexturePath)
                  if image.lower().endswith(".png") or image.lower().endswith(".png")]

        for image in images:
            imageKey = "%s/%s" % (self._cdnSubFolder, image)
            filePath = os.path.join(self.__channelTexturePath, image)

            if imageKey in textures:
                # verify the MD5 in the textures.md5
                md5 = self.__GetHash(filePath)
                if md5 == textures[imageKey]:
                    if self._logger is not None:
                        self._logger.Trace("Texture up to date: %s", filePath)
                else:
                    if self._logger is not None:
                        self._logger.Warning("Texture expired: %s", filePath)
                    os.remove(filePath)
            else:
                if self._logger is not None:
                    self._logger.Warning("Texture no longer required: %s", filePath)
                os.remove(filePath)
        return

    def __GetHash(self, filePath):
        hashObject = hashlib.md5()
        with open(filePath, "rb") as fs:
            for block in iter(lambda: fs.read(65536), ""):
                hashObject.update(block)
        md5 = hashObject.hexdigest()
        return md5
