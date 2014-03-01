#Taken from:
#https://www.bouncycastle.org/wiki/display/JA1/X.509+Public+Key+Certificate+and+Certification+Request+Generation

from java.security import Security, KeyPairGenerator, KeyFactory
from java.security.cert import CertificateFactory
from javax.security.auth.x500 import X500Principal

from java.io import ByteArrayInputStream, FileOutputStream
from java.util import Calendar
from java.math import BigInteger

from org.bouncycastle.x509 import X509V1CertificateGenerator
from org.bouncycastle.jce.provider import BouncyCastleProvider

from java.security.spec import X509EncodedKeySpec

import array
import java

Security.addProvider(BouncyCastleProvider())

def ca_do_everything(DevicePublicKey):
    keyPairGenerator = KeyPairGenerator.getInstance("RSA")
    keyPairGenerator.initialize(2048)
    keyPair = keyPairGenerator.genKeyPair()

    calendar = Calendar.getInstance()
    startDate = calendar.getTime()
    calendar.add(Calendar.YEAR, 10)
    expiryDate = calendar.getTime()

    certGen = X509V1CertificateGenerator()
    dnName = X500Principal("CN=Test CA Certificate")

    certGen.setSerialNumber(BigInteger.ONE)
    certGen.setIssuerDN(dnName)
    certGen.setNotBefore(startDate)
    certGen.setNotAfter(expiryDate)
    certGen.setSubjectDN(dnName)
    certGen.setPublicKey(keyPair.getPublic())
    certGen.setSignatureAlgorithm("SHA1withRSA")

    #FIXME: Find a way to generate DER certificate
    #For some reason, Java doesn't like PEM format
    #I can't load DevicePublicKey as PEM
    #
    #Maybe we can use BouncyCastle for this?

    f = java.io.File("pub.der")
    fis = java.io.FileInputStream(f)
    dis = java.io.DataInputStream(fis)
    keyBytes = array.zeros("b",f.length())
    dis.readFully(keyBytes)
    dis.close()

    spec = X509EncodedKeySpec(keyBytes)
    kf = KeyFactory.getInstance("RSA")
    pubKey = kf.generatePublic(spec)

    cert = "-----BEGIN CERTIFICATE-----\n" + certGen.generate(keyPair.getPrivate(), "BC").getEncoded().tostring().encode("base64") + "\n-----END CERTIFICATE-----\n"

    key = "-----BEGIN PRIVATE KEY-----\n" + keyPair.getPrivate().getEncoded().tostring().encode("base64") + "\n-----END PRIVATE KEY-----\n"
    
    certGen.setPublicKey(pubKey)
    dnName = X500Principal("CN=Device")
    certGen.setSubjectDN(dnName)

    cert2  = "-----BEGIN CERTIFICATE-----\n" + certGen.generate(keyPair.getPrivate(), "BC").getEncoded().tostring().encode("base64") + "\n-----END CERTIFICATE-----\n"

    return cert, key, cert2
