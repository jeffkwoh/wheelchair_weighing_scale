#include <PN532.h>
#include <PN532_HSU.h>
#include <NfcAdapter.h>

#define DEFAULT_WHEELCHAIR_DATA " :2000"
#define LIBRARY_TEXT_RECORD_PREFIX "\02en"

PN532_HSU pn532hsu(Serial1);
NfcAdapter nfc = NfcAdapter(pn532hsu);  // Indicates the Shield you are using

void setup(void) {
  Serial.begin(9600);
  Serial.println("RESET TAG");
  nfc.begin();
}

/**
* Converts an NdefMessage into its String representation for outputting via serial
*
*/
void extractMessage(NdefMessage message, String &target) {
  target = "";
  // If you have more than 1 Message then it will cycle through them
  int recordCount = message.getRecordCount();
  for (int i = 0; i < recordCount; i++) {
    NdefRecord record = message.getRecord(i);

    int payloadLength = record.getPayloadLength();
    byte payload[payloadLength];
    record.getPayload(payload);

    String payloadAsString = ""; // Processes the message as a string vs as a HEX value
    for (int c = 0; c < payloadLength; c++) {
      byte b = payload[c];
      // Sanity check, ACSII only
      if (b < 128 && b >= 0) {
        payloadAsString += (char)payload[c]; 
      }          
    }

    payloadAsString.replace(LIBRARY_TEXT_RECORD_PREFIX, "");

    target += payloadAsString; 
  }

}

void loop(void) {

  if (nfc.tagPresent())
  {
    NdefMessage message = NdefMessage();
    message.addTextRecord(DEFAULT_WHEELCHAIR_DATA);
    nfc.write(message);

    NfcTag tag = nfc.read();
    if (tag.hasNdefMessage()) // If your tag has a message
    {

      NdefMessage message = tag.getNdefMessage();

      String toPrint;
      extractMessage(message, toPrint);
      Serial.println(toPrint);
    }
  }
  delay(1000); // Variable delay to tweak and find the Magic Number
}
