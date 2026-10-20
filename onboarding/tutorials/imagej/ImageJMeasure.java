import ij.IJ;
import ij.ImagePlus;
import ij.Prefs;
import ij.measure.Calibration;
import ij.measure.Measurements;
import ij.measure.ResultsTable;
import ij.plugin.filter.ParticleAnalyzer;
import ij.plugin.filter.Binary;
import ij.process.ByteProcessor;
import ij.process.ImageProcessor;
import java.awt.image.BufferedImage;
import java.nio.file.Path;
import java.util.Arrays;
import javax.imageio.ImageIO;

/** One reviewed binary mask per invocation. No detection or marker classification. */
public final class ImageJMeasure {
    public static void main(String[] args) throws Exception {
        if (args.length != 5) throw new IllegalArgumentException("mask width height pixelWidthUm pixelHeightUm");
        if (!IJ.getVersion().equals("1.54p")) throw new IllegalStateException("Wrong ImageJ version");
        int width = Integer.parseInt(args[1]), height = Integer.parseInt(args[2]);
        double pw = Double.parseDouble(args[3]), ph = Double.parseDouble(args[4]);
        if (width < 1 || height < 1 || !Double.isFinite(pw) || !Double.isFinite(ph) || pw <= 0 || ph <= 0
                || !Double.isFinite(pw * ph) || pw * ph == 0)
            throw new IllegalArgumentException("Invalid dimensions/calibration");
        BufferedImage image = ImageIO.read(Path.of(args[0]).toFile());
        if (image == null || image.getWidth() != width || image.getHeight() != height
                || image.getRaster().getNumBands() != 1 || image.getSampleModel().getSampleSize(0) != 8)
            throw new IllegalArgumentException("Expected declared dimensions and 8-bit grayscale PNG");
        byte[] pixels = new byte[width * height];
        for (int y = 0; y < height; y++) for (int x = 0; x < width; x++) {
            int value = image.getRaster().getSample(x, y, 0);
            if (value != 0 && value != 255) throw new IllegalArgumentException("Mask must contain only 0 and 255");
            pixels[y * width + x] = (byte)value;
        }
        ByteProcessor processor = new ByteProcessor(width, height, pixels, null);
        // Validate filled-region semantics using ImageJ's own Fill Holes on a disposable copy.
        // This detects background not 4-connected to an image edge, complementary to 8-connected objects.
        ByteProcessor filled = (ByteProcessor)processor.duplicate();
        Prefs.blackBackground = true; // This short-lived process never saves preferences.
        Binary fillHoles = new Binary();
        fillHoles.setup("fill", new ImagePlus("validation-copy", filled));
        fillHoles.run(filled);
        if (!Arrays.equals(pixels, (byte[])filled.getPixels()))
            throw new IllegalArgumentException("Mask contains enclosed holes; supply filled reviewed regions");
        processor.setThreshold(255, 255, ImageProcessor.NO_LUT_UPDATE);
        ImagePlus imp = new ImagePlus("reviewed-mask", processor);
        Calibration cal = new Calibration();
        cal.setUnit("um"); cal.pixelWidth = pw; cal.pixelHeight = ph;
        imp.setCalibration(cal);
        ResultsTable table = new ResultsTable();
        // Filled reviewed regions only; default 8-connectivity, include edge objects, no size filtering.
        ParticleAnalyzer analyzer = new ParticleAnalyzer(ParticleAnalyzer.SHOW_NONE,
                Measurements.AREA, table, 0.0, Double.MAX_VALUE);
        if (!analyzer.analyze(imp)) throw new IllegalStateException("ImageJ particle analysis failed");
        System.err.println("ImageJ=" + IJ.getVersion() + " java=" + System.getProperty("java.runtime.version"));
        System.out.println("object_index,area_um2");
        for (int i = 0; i < table.size(); i++) {
            double area = table.getValue("Area", i);
            if (!Double.isFinite(area) || area <= 0) throw new IllegalStateException("Invalid ImageJ area");
            System.out.println((i + 1) + "," + Double.toString(area));
        }
        imp.close();
    }
}
