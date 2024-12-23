"""
Python library for interacting with WebWar archives
"""

import os
from enum import Enum
from pathlib import Path
import zipfile

class AssetNotFoundError(Exception):
	pass

class UnknownArchiveFormatError(Exception):
	pass

class ArchiveAssetManager:
	"""
	Read an archive as a directory on the file system
	"""
	
	def __init__(self, path, read_only=False):
		self.path = path
	
	def read(self, path):
		"""
		Read a file
		"""
		
		p = Path(f"{self.path}/{path}")
		
		if not p.is_file():
			raise AssetNotFoundError()
		
		return p.read_bytes()
	
	def write(self, path, content):
		"""
		Write a file
		"""
		
		p = Path(f"{self.path}/{path}")
		os.makedirs(p.parent, exist_ok=True)
		p.write_bytes(bytes(content, 'utf-8') if type(content) == str else content)
	
	@staticmethod
	def may_match(path):
		"""
		Infer if the path may be used with this type of asset manager
		"""
		
		return Path(path).is_dir()

class ZipArchiveAssetManager:
	"""
	An asset manager for archives stored as zip files
	"""
	
	def __init__(self, path, read_only=False):
		self.z = zipfile.ZipFile(path, mode='r' if read_only else 'a')
	
	def read(self, path):
		if not zipfile.Path(self.z, path).is_file():
			raise AssetNotFoundError()
		
		return self.z.read(path)
	
	def write(self, path, content):
		self.z.writestr(path, content)
	
	@staticmethod
	def may_match(path):
		return Path(path).is_file() and path.lower().endswith(".zip")

ASSET_MANAGER_TYPES = [
	ArchiveAssetManager,
	ZipArchiveAssetManager,
]

class Archive:
	"""
	An archive of a collection of requests
	"""
	
	def __init__(self, path, read_only=False):
		self.path = path
		
		for amt in ASSET_MANAGER_TYPES:
			if amt.may_match(path):
				self.asset_manager = amt(path, read_only)
				self.asset_manager_type = amt.__name__
				break
		else:
			raise UnknownArchiveFormatError("Unknown archive format")
	
	def __repr__(self):
		return f"<{self.__class__.__name__}: {self.asset_manager_type} {repr(self.path)}>"
	
	def read(self, path):
		return self.asset_manager.read(path)
	
	def write(self, path, content):
		self.asset_manager.write(path, content)
	
