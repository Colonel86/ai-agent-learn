# L2: Role of the Tokenizers

<p style="background-color:#fff6e4; padding:15px; border-width:3px; border-color:#f5ecda; border-style:solid; border-radius:6px"> ⏳ <b>Note <code>(Kernel Starting)</code>:</b> This notebook takes about 30 seconds to be ready to use. You may start and watch the video while you wait.</p>


```python
import warnings
warnings.filterwarnings('ignore')
```


```python
training_data = [
    "walker walked a long walk",
]
```

## BPE - Byte-Pair Encoding


```python
from tokenizers.trainers import BpeTrainer
from tokenizers.models import BPE
from tokenizers import Tokenizer
from tokenizers.pre_tokenizers import Whitespace

bpe_tokenizer = Tokenizer(BPE())
bpe_tokenizer.pre_tokenizer = Whitespace()

bpe_trainer = BpeTrainer(vocab_size=14)
```

<p style="background-color:#fff6ff; padding:15px; border-width:3px; border-color:#efe6ef; border-style:solid; border-radius:6px"> 💻 &nbsp; <b>Access <code>requirements.txt</code> and <code>helper.py</code> files:</b> 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Open"</em>. For more help, please see the <em>"Appendix - Tips and Help"</em> Lesson.</p>


```python
bpe_tokenizer.train_from_iterator(training_data, bpe_trainer)
```


```python
bpe_tokenizer.get_vocab()
```


```python
bpe_tokenizer.encode("walker walked a long walk").tokens
```


```python
bpe_tokenizer.encode("wlk").ids
```


```python
bpe_tokenizer.encode("wlk").tokens
```


```python
bpe_tokenizer.encode("she walked").tokens
```

## WordPiece


```python
from real_wordpiece.trainer import RealWordPieceTrainer
from tokenizers.models import WordPiece

real_wordpiece_tokenizer = Tokenizer(WordPiece())
real_wordpiece_tokenizer.pre_tokenizer = Whitespace()

real_wordpiece_trainer = RealWordPieceTrainer(
    vocab_size=27,
)
```


```python
real_wordpiece_trainer.train_tokenizer(
    training_data, real_wordpiece_tokenizer
)
real_wordpiece_tokenizer.get_vocab()
```


```python
real_wordpiece_tokenizer.encode("walker walked a long walk").tokens
```


```python
real_wordpiece_tokenizer.encode("wlk").tokens
```

**Unknown Characters:**
The following line will produce an error because it contains unknown characters. Please uncomment the line and run it to see the error.


```python
#real_wordpiece_tokenizer.encode("she walked").tokens
```

## HuggingFace WordPiece and special tokens


```python
from tokenizers.trainers import WordPieceTrainer

unk_token = "[UNK]"

wordpiece_model = WordPiece(unk_token=unk_token)
wordpiece_tokenizer = Tokenizer(wordpiece_model)
wordpiece_tokenizer.pre_tokenizer = Whitespace()
wordpiece_trainer = WordPieceTrainer(
    vocab_size=28,
    special_tokens=[unk_token]
)
```


```python
wordpiece_tokenizer.train_from_iterator(
    training_data, 
    wordpiece_trainer
)
wordpiece_tokenizer.get_vocab()
```


```python
wordpiece_tokenizer.encode("walker walked a long walk").tokens
```


```python
wordpiece_tokenizer.encode("wlk").tokens
```


```python
wordpiece_tokenizer.encode("she walked").tokens
```

## Unigram


```python
from tokenizers.trainers import UnigramTrainer
from tokenizers.models import Unigram

unigram_tokenizer = Tokenizer(Unigram())
unigram_tokenizer.pre_tokenizer = Whitespace()
unigram_trainer = UnigramTrainer(
    vocab_size=14, 
    special_tokens=[unk_token],
    unk_token=unk_token,
)

unigram_tokenizer.train_from_iterator(training_data, unigram_trainer)
unigram_tokenizer.get_vocab()
```


```python
unigram_tokenizer.encode("walker walked a long walk").tokens
```


```python
unigram_tokenizer.encode("wlk").tokens
```


```python
unigram_tokenizer.encode("she walked").tokens
```


```python
unigram_tokenizer.encode("she walked").ids
```


```python

```


```python

```


```python

```


```python

```


```python

```


```python

```


```python

```
