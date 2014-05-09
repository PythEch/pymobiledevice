#
# pymobiledevice - Jython implementation of libimobiledevice
#
# Copyright (C) 2014  Taconut <https://github.com/Triforce1>
# Copyright (C) 2014  PythEch <https://github.com/PythEch>
# Copyright (C) 2013  GotoHack <https://github.com/GotoHack>
#
# pymobiledevice is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pymobiledevice is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with pymobiledevice.  If not, see <http://www.gnu.org/licenses/>.


from java.security import Security, KeyPairGenerator, KeyFactory
from javax.security.auth.x500 import X500Principal
from java.security.spec import X509EncodedKeySpec

from java.util import Calendar
from java.math import BigInteger

from org.bouncycastle.x509 import X509V1CertificateGenerator
from org.bouncycastle.jce.provider import BouncyCastleProvider

Security.addProvider(BouncyCastleProvider())


def convertPKCS1toPKCS8pubKey(data):
    subjectpublickeyrsa_start = "30 81 9E 30 0D 06 09 2A 86 48 86 F7 0D 01 01 01 05 00 03 81 8C 00".replace(" ", "").decode("hex")
    data = data.replace("-----BEGIN RSA PUBLIC KEY-----", "").replace("-----END RSA PUBLIC KEY-----", "").decode('base64')
    if data.startswith("30 81 89 02 81 81 00".replace(" ", "").decode("hex")):
        #HAX remove null byte to make 128 bytes modulus
        data = "30 81 88 02 81 80".replace(" ", "").decode("hex") + data[7:]
    return subjectpublickeyrsa_start + data


def ca_do_everything(DevicePublicKey):
    # Generate random 2048-bit private and public keys
    keyPairGenerator = KeyPairGenerator.getInstance("RSA")
    keyPairGenerator.initialize(2048)
    keyPair = keyPairGenerator.genKeyPair()

    # Make it valid for 10 years
    calendar = Calendar.getInstance()
    startDate = calendar.getTime()
    calendar.add(Calendar.YEAR, 10)
    expiryDate = calendar.getTime()

    certGen = X509V1CertificateGenerator()
    dnName = X500Principal("CN=Pymobiledevice Self-Signed CA Certificate")

    certGen.setSerialNumber(BigInteger.ONE)
    certGen.setIssuerDN(dnName)
    certGen.setNotBefore(startDate)
    certGen.setNotAfter(expiryDate)
    certGen.setSubjectDN(dnName)  # subject = issuer
    certGen.setPublicKey(keyPair.getPublic())
    certGen.setSignatureAlgorithm("SHA1withRSA")

    #Load PKCS#1 RSA Public Key
    spec = X509EncodedKeySpec(convertPKCS1toPKCS8pubKey(DevicePublicKey))
    pubKey = KeyFactory.getInstance("RSA").generatePublic(spec)

    certPem = "-----BEGIN CERTIFICATE-----\n" + certGen.generate(keyPair.getPrivate(), "BC").getEncoded().tostring().encode("base64") + "-----END CERTIFICATE-----\n"

    privateKeyPem = "-----BEGIN PRIVATE KEY-----\n" + keyPair.getPrivate().getEncoded().tostring().encode("base64") + "-----END PRIVATE KEY-----\n"

    certGen.setPublicKey(pubKey)
    dnName = X500Principal("CN=Pymobiledevice Self-Signed Device Certificate")
    certGen.setSubjectDN(dnName)

    DeviceCertificate = "-----BEGIN CERTIFICATE-----\n" + certGen.generate(keyPair.getPrivate(), "BC").getEncoded().tostring().encode("base64") + "-----END CERTIFICATE-----\n"

    return certPem, privateKeyPem, DeviceCertificate
