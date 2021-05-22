#!/usr/bin/python3

# Imports
import sys
import time
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator
from bip_utils import Bip44, Bip44Changes, Bip44Coins
from bip_utils import Bip49
from bip_utils import Bip84
#from utils     import *
from bs4 import BeautifulSoup
import requests as req
from time import perf_counter

file = open("file_key.txt","a+")   

#
# Constants
#

# Allowed arguments
ALLOWED_ARGS       = ("bip44", "bip49", "bip84")
# Map from argument to Bip class type
ARG_TO_BIP_CLASSES = { "bip44" : Bip44, "bip49" : Bip49, "bip84" : Bip84 }
# Number of words to generate mnemonic
MNEMONIC_WORDS_NUM = 12
# Account index for keys derivation
ACCOUNT_IDX        = 0
# Chain type for keys derivation
CHANGE_TYPE        = Bip44Changes.CHAIN_EXT
# Number of address to be check for a wallet
ADDRESS_MAX_NUM    = 20
# Time to sleep after each address check
SLEEP_TIME         = 0.3

#
# Functions
#

# Validate arguments
def query(address,bip_obj_mst,mnemonic,bip_obj_acc):
    url="https://www.blockchain.com/btc/address/"+address
    page=req.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    a=soup.find_all('span',class_="sc-1ryi78w-0 cILyoi sc-16b9dsl-1 ZwupP u3ufsr-0 eQTRKC")
    count=0
    for i in a:
        for j in i:
            count+=1
            if(count==6):
            # print(i.contents[0].split(" ")[0])
                    print("balance is "+i.contents[0].split(" ")[0]+ " for "+address)
                    if float(i.contents[0].split(" ")[0]):  # comment line 26 and 27 if u dont want to stop if balance is greater than 0 for an address 
                        file.writelines("Mnemonic: %s" % mnemonic)
                        file.writelines("\n")
                        file.writelines("Master key WIF     : %s"  % bip_obj_mst.PrivateKey().ToWif())
                        file.writelines("\n")
                        file.writelines("Master key         : %s"  % bip_obj_mst.PrivateKey().ToExtended())
                        file.writelines("\n")
                        file.writelines("Account private key: %s"  % bip_obj_acc.PrivateKey().ToExtended())
                        file.writelines("\n")
                        file.writelines("Account public key : %s"  % bip_obj_acc.PublicKey().RawUncompressed().ToHex())
                        file.writelines("\n")
                        file.writelines("Scanning the first %d addresses..." % ADDRESS_MAX_NUM)
                        file.writelines("\n --------- \n")
    

def validate_args(argv):
    return len(argv) == 1 and argv[0] in ALLOWED_ARGS

# Print usage
def print_usage():
    print("Usage:")
    print("  python main.py <BIP_CLASS>")
    print("Where BIP_CLASS = bip44, bip49 or bip84")
    print("Example:")
    print("  python main.py bip44")

# Main function
def main(argv):
    # Check if arguments are valid
    if not validate_args(argv):
        print_usage()
        sys.exit(1)

    # Get BIP class to be used from argument
    bip_class = ARG_TO_BIP_CLASSES[argv[0]]

    itr_num = 1
    stop    = False
    # Main loop
    while not stop:
        # Generate random mnemonic
        mnemonic = Bip39MnemonicGenerator().FromWordsNumber(MNEMONIC_WORDS_NUM)
        # Generate seed from mnemonic
        seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
        # Generate master key from seed
        bip_obj_mst = bip_class.FromSeed(seed_bytes,Bip44Coins.BITCOIN)
        # Generate account keys
        bip_obj_acc = bip_obj_mst.Purpose().Coin().Account(ACCOUNT_IDX)
        # Generate chain keys
        bip_obj_chain = bip_obj_acc.Change(CHANGE_TYPE)
        # Print
        print("******************** ITERATION %d ********************" % itr_num)
        print("Mnemonic: %s" % mnemonic)
        print("Master key WIF     : %s"  % bip_obj_mst.PrivateKey().ToWif())
        print("Master key         : %s"  % bip_obj_mst.PrivateKey().ToExtended())
        print("Account private key: %s"  % bip_obj_acc.PrivateKey().ToExtended())
        print("Account public key : %s"  % bip_obj_acc.PublicKey().RawUncompressed().ToHex())
        print("Scanning the first %d addresses..." % ADDRESS_MAX_NUM)


        # Check the addresses
        i = 0
        while i < ADDRESS_MAX_NUM and not stop:
            try:
                # Derive address keys
                bip_obj_addr = bip_obj_chain.AddressIndex(i)
                # Get address string
                addr_str = bip_obj_addr.PublicKey().ToAddress().strip()
                query(addr_str,bip_obj_mst,mnemonic,bip_obj_acc)

               
                i += 1

            # Error in generating address keys
            except Exception:
                i += 1
                print("Unable to save address data to file")

            # Sleep some time
            time.sleep(SLEEP_TIME)


# Execute main
if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    # Stop if CTRL+C is pressed
    except KeyboardInterrupt:
        file.close()
        print("CTRL+C pressed, stopping...")
