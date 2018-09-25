from periphery import MMIO as _MMIO_
import math


def _i2lg_bits(ival, bfrom, bto):
	bits = '{0:b}'.format(ival)
	bits = '0'*((8 - bto % 8) % 8) + bits.rjust(bto - bfrom, '0') + '0'*bfrom
	return bits[::-1]


def _b2lg_bits(bts):
	result = ''
	for b in bts:
		result += '{0:b}'.format(b).rjust(8, '0')[::-1]
	return result


def _write(dest, source, bfrom, bto):
	result = ''
	for i in range(0, len(dest)):
		if i < bfrom or i > bto:
			result += dest[i]
		else:
			result += source[i]
	return result


def _lgb2bytes(lg):
	result = b''
	for i in range(0, len(lg), 8):
		bts = lg[i:i+8][::-1]
		result += bytes([int(bts, 2)])
	return result


def _bytes2int(bts):
	result = 0
	m = 1
	for b in bts:
		result += m*b
		m *= 256
	return result


def __lgb2int(lg):
	return _bytes2int(_lgb2bytes(lg))


class MMIOBitIndexer:
	def __init__(self, mmio, offset, bfrom, bto):
		self.__mmio = mmio
		self.__offset = offset
		self.__bfrom = bfrom
		self.__bto = bto

	def int(self):
		return _bytes2int(self.bytes())

	def bytes_array(self):
		return [i for i in self.bytes()]

	def bits(self):
		return _b2lg_bits(self.bytes())

	def bytes(self):
		return self.__mmio.readB(self.__offset, self.__bfrom, self.__bto)


class MMIOIndexer:
	def __init__(self, mmio, offset, toNI=None):
		self.__mmio = mmio
		self.__offset = offset
		self.__toNI = toNI

	def int(self):
		return _bytes2int(self.bytes())

	def bytes_array(self):
		return [i for i in self.bytes()]

	def bytes(self):
		return self.__mmio.read(self.__offset, self.__toNI - self.__offset)

	def bits(self):
		return _b2lg_bits(self.bytes())

	def __getitem__(self, key): 
		return MMIOBitIndexer(self.__mmio, self.__offset, key.start, key.stop)

	def __setitem__(self, key, value):
		self.__mmio.writeB(self.__offset, key.start, key.stop, value)

class MMIO(_MMIO_):
	def __init__(self, addr, count):
		super().__init__(addr, count)

	def readI(self, offset, length):
		return [int(b) for b in self.read(offset, length)]

	def readB(self, offset, bfrom, bto):
		if bto < bfrom:
			bto, bfrom = bfrom, bto
		bts = self.read(offset, math.ceil(bto/8))	
		return _lgb2bytes(_b2lg_bits(bts)[bfrom:bto])

	def readBI(self, offset, bfrom, bto):
		return _bytes2int(self.readB(offset, bfrom, bto))

	def writeB(self, offset, bfrom, bto, value):
		if bto < bfrom:
			bto, bfrom = bfrom, bto
		bts = self.read(offset, math.ceil(bto/8))
		src = _i2lg_bits(value, bfrom, bto) if isinstance(value, int) else _b2lg_bits(value)
		to_write = _lgb2bytes(_write(_b2lg_bits(bts), src, bfrom, bto))
		self.write(offset, to_write)
		
	def __getitem__(self, key):
		if isinstance(key, slice):
			return MMIOIndexer(self, key.start, key.stop)
		return MMIOIndexer(self, key)

	def __setitem__(self, offset, value):
		self.write(offset, value)