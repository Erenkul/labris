"""
Substitution Ciphers: Replace individual letters or groups of letters
 with other letters or symbols (e.g., the Caesar Cipher shifts alphabet 
 letters by a fixed number).
"""


def caesar_cipher(text, shift, mode='encrypt'):
    """
    Encrypts or decrypts text using the Caesar cipher technique.
    
    :param text: str - The message to be transformed
    :param shift: int - The number of positions to shift the alphabet
    :param mode: str - Either 'encrypt' or 'decrypt'
    :return: str - The final transformed message
    """
    result = ""
    
    # Reverse the shift direction if we are decrypting
    if mode == 'decrypt':
        shift = -shift
        
    for char in text:
        # Process uppercase letters
        if char.isupper():
            # Shift within the A-Z ASCII range (65-90)
            result += chr((ord(char) + shift - 65) % 26 + 65)
        # Process lowercase letters
        elif char.islower():
            # Shift within the a-z ASCII range (97-122)
            result += chr((ord(char) + shift - 97) % 26 + 97)
        else:
            # Leave punctuation, numbers, and spaces as they are
            result += char
            
    return result

# --- Example Usage ---
if __name__ == "__main__":
    message = "Hello, World! 2026"
    key = 4
    
    # 1. Encrypt the message
    encrypted_msg = caesar_cipher(message, key, mode='encrypt')
    print(f"Original:  {message}")
    print(f"Encrypted: {encrypted_msg}")
    
    # 2. Decrypt it back
    decrypted_msg = caesar_cipher(encrypted_msg, key, mode='decrypt')
    print(f"Decrypted: {decrypted_msg}")