using System;
using System.IO;
using Windows.Foundation;
using Windows.Graphics.Imaging;
using Windows.Media.Ocr;
using Windows.Storage;

public class Program
{
    [STAThread]
    public static void Main(string[] args)
    {
        if (args.Length == 0)
        {
            Console.WriteLine("ERROR: Thieu duong dan tep anh!");
            return;
        }

        string imagePath = args[0];
        if (!File.Exists(imagePath))
        {
            Console.WriteLine("ERROR: Khong tim thay tep anh: " + imagePath);
            return;
        }

        try
        {
            string fullPath = Path.GetFullPath(imagePath);
            
            var fileOp = StorageFile.GetFileFromPathAsync(fullPath);
            while (fileOp.Status == AsyncStatus.Started) System.Threading.Thread.Sleep(10);
            if (fileOp.Status == AsyncStatus.Error) throw fileOp.ErrorCode;
            StorageFile file = fileOp.GetResults();
            
            var streamOp = file.OpenAsync(FileAccessMode.Read);
            while (streamOp.Status == AsyncStatus.Started) System.Threading.Thread.Sleep(10);
            if (streamOp.Status == AsyncStatus.Error) throw streamOp.ErrorCode;
            var stream = streamOp.GetResults();
            
            var decoderOp = BitmapDecoder.CreateAsync(stream);
            while (decoderOp.Status == AsyncStatus.Started) System.Threading.Thread.Sleep(10);
            if (decoderOp.Status == AsyncStatus.Error) throw decoderOp.ErrorCode;
            BitmapDecoder decoder = decoderOp.GetResults();
            
            var bitmapOp = decoder.GetSoftwareBitmapAsync();
            while (bitmapOp.Status == AsyncStatus.Started) System.Threading.Thread.Sleep(10);
            if (bitmapOp.Status == AsyncStatus.Error) throw bitmapOp.ErrorCode;
            SoftwareBitmap softwareBitmap = bitmapOp.GetResults();
            
            OcrEngine engine = OcrEngine.TryCreateFromUserProfileLanguages();
            if (engine == null)
            {
                throw new Exception("Khong the khoi tao OcrEngine cua Windows");
            }
            
            var ocrOp = engine.RecognizeAsync(softwareBitmap);
            while (ocrOp.Status == AsyncStatus.Started) System.Threading.Thread.Sleep(10);
            if (ocrOp.Status == AsyncStatus.Error) throw ocrOp.ErrorCode;
            OcrResult ocrResult = ocrOp.GetResults();
            
            Console.OutputEncoding = System.Text.Encoding.UTF8;
            foreach (var line in ocrResult.Lines)
            {
                Console.WriteLine(line.Text);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine("ERROR: " + ex.ToString());
        }
    }
}
