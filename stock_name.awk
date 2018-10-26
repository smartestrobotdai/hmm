#!/bin/awk
{
  if ($NF == "B" || $NF=="A") {
    printf("%s-%s", $(NF-1), $NF)
  } else {
    printf("%s", $NF)
  }
}