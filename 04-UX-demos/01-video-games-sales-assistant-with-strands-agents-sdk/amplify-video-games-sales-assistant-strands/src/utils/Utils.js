export const extractBetweenTags = (string, tag) => {
  const startTag = `<${tag}>`;
  const endTag = `</${tag}>`;
  const startIndex = string.indexOf(startTag) + startTag.length;
  const endIndex = string.indexOf(endTag, startIndex);
  if (startIndex === -1 || endIndex === -1) {
    return "";
  }
  return string.slice(startIndex, endIndex);
};

export const removeCharFromStartAndEnd = (str, charToRemove) => {
  // Check if the string starts with the character
  while (str.startsWith(charToRemove)) {
    str = str.substring(1);
  }
  // Check if the string ends with the character
  while (str.endsWith(charToRemove)) {
    str = str.substring(0, str.length - 1);
  }
  return str;
};

export const handleFormatter = (obj) => {
  if (typeof obj === "object" && obj !== null) {
    for (let key in obj) {
      if (typeof obj[key] === "string") {
        if (
          key === "formatter" &&
          (obj[key] === "%" || obj[key].startsWith("$"))
        ) {
          handleFormatter(obj[key]);
          // Convert the function string to an actual function
        } else if (key === "formatter") {
          obj[key] = new Function("return " + obj[key])();
        } else {
          handleFormatter(obj[key]);
        }
      } else if (typeof obj[key] === "object") {
        handleFormatter(obj[key]);
      }
    }
  }
  return obj;
};
