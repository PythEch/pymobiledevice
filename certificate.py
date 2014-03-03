#Taken from:
#https://www.bouncycastle.org/wiki/display/JA1/X.509+Public+Key+Certificate+and+Certification+Request+Generation

from java.security import Security, KeyPairGenerator, KeyFactory
from java.security.cert import CertificateFactory
from javax.security.auth.x500 import X500Principal
from java.security.spec import X509EncodedKeySpec

from java.util import Calendar
from java.math import BigInteger

from org.bouncycastle.x509 import X509V1CertificateGenerator
from org.bouncycastle.jce.provider import BouncyCastleProvider

import base64

Security.addProvider(BouncyCastleProvider())

def convertPKCS1toPKCS8pubKey(data):
    """
    Copyright (c) 2004 Open Source Applications Foundation.
    Author: Heikki Toivonen
    """
    subjectpublickeyrsa_start = "30 81 9E 30 0D 06 09 2A 86 48 86 F7 0D 01 01 01 05 00 03 81 8C 00".replace(" ","").decode("hex")
    data = data.replace("-----BEGIN RSA PUBLIC KEY-----", "").replace("-----END RSA PUBLIC KEY-----", "")
    data = base64.b64decode(data)
    if data.startswith("30 81 89 02 81 81 00".replace(" ","").decode("hex")):
        #HAX remove null byte to make 128 bytes modulus
        data = "30 81 88 02 81 80".replace(" ","").decode("hex") + data[7:]
    z = base64.b64encode(subjectpublickeyrsa_start + data)
    #res = "-----BEGIN PUBLIC KEY-----\n" # we'll use DER format
    res = ""
    for i in xrange(len(z)/64 + 1):
        res += z[i*64:(i+1)*64] + "\n"
    #res += "-----END PUBLIC KEY-----"
    return res

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
    certGen.setSubjectDN(dnName) # subject = issuer
    certGen.setPublicKey(keyPair.getPublic())
    certGen.setSignatureAlgorithm("SHA1withRSA")

    #Load PKCS#1 RSA Public Key
    spec = X509EncodedKeySpec(convertPKCS1toPKCS8pubKey(DevicePublicKey).decode("base64"))
    pubKey = KeyFactory.getInstance("RSA").generatePublic(spec)

    certPem = "-----BEGIN CERTIFICATE-----\n" + certGen.generate(keyPair.getPrivate(), "BC").getEncoded().tostring().encode("base64") + "-----END CERTIFICATE-----\n"

    privateKeyPem = "-----BEGIN PRIVATE KEY-----\n" + keyPair.getPrivate().getEncoded().tostring().encode("base64") + "-----END PRIVATE KEY-----\n"

    certGen.setPublicKey(pubKey)
    dnName = X500Principal("CN=Pymobiledevice Self-Signed Device Certificate")
    certGen.setSubjectDN(dnName)

    DeviceCertificate  = "-----BEGIN CERTIFICATE-----\n" + certGen.generate(keyPair.getPrivate(), "BC").getEncoded().tostring().encode("base64") + "-----END CERTIFICATE-----\n"

    return certPem, privateKeyPem, DeviceCertificate
